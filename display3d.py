

import platform
import os
import sys
import threading
import numpy as np
import config
from widgets.button import Button
from widgets.rgbselector import RGBSelector
from widgets.slider import Slider

PLATFORM    = platform.system()
IS_MACOS    = PLATFORM == "Darwin"
IS_LINUX    = PLATFORM == "Linux"
IS_WINDOWS  = PLATFORM == "Windows"
IS_SILICON  = IS_MACOS and (platform.machine() == "arm64")

EPS = 1e-6

class Display3D:
    
    def __init__(self, history, width=1000, height=800):
        self.width = width
        self.height = height
        self.history = np.array(history)
        self.chunk_size = 16
        self.cube_size = 0.48
        self.generations, self.size_x, self.size_y = self.history.shape
        pts_list = []

        for g in range(self.generations):
            x, y = np.where(self.history[g] == 1)
            z    = np.full_like(x, g)
            pts_list.append(np.column_stack((x, y, z)).astype(np.float32))

        self.all_points = np.vstack(pts_list)
        self.N = len(self.all_points)

        self.CX = self.size_x        / 2.0
        self.CY = self.size_y        / 2.0
        self.CZ = self.generations

        self.base_dist = max(self.size_x, self.size_y) / 1.2
        self.zoom_min  = 5.0

        print(f"[Platform] {PLATFORM} {'(Apple Silicon)' if IS_SILICON else ''}")
        print(f"[Sim] Generaciones: {self.generations}, Células vivas: {self.N}")

        self.use_wgpu = False
    
    def perspective(self, fov_deg, aspect, near, far):
        f = 1.0 / np.tan(np.radians(fov_deg) / 2)
        return np.array([
            [f/aspect, 0,  0,                         0                      ],
            [0,        f,  0,                         0                      ],
            [0,        0,  (far+near)/(near-far),     (2*far*near)/(near-far)],
            [0,        0,  -1,                        0                      ],
        ], dtype=np.float32)

    def translate(self, tx, ty, tz):
        m = np.eye(4, dtype=np.float32)
        m[:3, 3] = [tx, ty, tz]
        return m

    def rot_x_mat(self, deg):
        a = np.radians(deg); c, s = float(np.cos(a)), float(np.sin(a))
        return np.array([[1,0,0,0],[0,c,-s,0],[0,s,c,0],[0,0,0,1]], dtype=np.float32)

    def rot_y_mat(self, deg):
        a = np.radians(deg); c, s = float(np.cos(a)), float(np.sin(a))
        return np.array([[c,0,s,0],[0,1,0,0],[-s,0,c,0],[0,0,0,1]], dtype=np.float32)

    def compute_mvp(self,rx, ry, dist, cam_x, cam_y, cam_z):
        proj  = self.perspective(45, 1000/800, 0.1, 1000.0)
        view = self.translate(-cam_x, -cam_y, -dist - cam_z) @ self.translate(-self.CX, -self.CY, -self.CZ)
        model = self.translate(self.CX,self.CY,self.CZ) @ self.rot_y_mat(ry) @ self.rot_x_mat(rx) @ self.translate(-self.CX,-self.CY,-self.CZ)
        return proj @ view @ model
    
    def extract_frustum_planes(self, m):
        planes = [
            m[3] + m[0],
            m[3] - m[0],
            m[3] + m[1],
            m[3] - m[1],
            m[3] + m[2],
            m[3] - m[2],
        ]
        out = []
        for p in planes:
            n = p[:3]
            l = np.linalg.norm(n)
            if l > EPS:
                out.append(p / l)
            else:
                continue
        if len(out) != 6:
            print("Warning: frustum incompleto:", len(out))
        return out

    def aabb_in_frustum_minmax(self, planes, min_p, max_p):
        for p in planes:
            n = p[:3]
            d = p[3]

            # seleccionar vértice extremo directamente
            p_vertex = np.where(n > 0, max_p, min_p)

            if np.dot(n, p_vertex) + d < 0:
                return False

        return True

    def get_chunks(self):
        # Calcular las coordenadas de los chunks de forma vectorizada
        all_points = np.asarray(self.all_points)
        coords = (all_points // self.chunk_size).astype(np.int32)

        # Ordenar los puntos según sus coordenadas de chunk (lexicográficamente)
        sort_idx = np.lexsort((coords[:, 2], coords[:, 1], coords[:, 0]))
        sorted_points = all_points[sort_idx]
        sorted_coords = coords[sort_idx]

        # Encontrar los límites donde cambia un chunk de otro
        diffs = np.any(np.diff(sorted_coords, axis=0) != 0, axis=1)
        # Obtenemos los índices de inicio de cada bloque
        boundaries = np.concatenate(([0], np.where(diffs)[0] + 1, [len(sorted_points)]))

        chunk_data = {}
        chunk_bounds = {}

        #Extraer los datos usando 'reduceat' para los mínimos y máximos
        unique_keys = sorted_coords[boundaries[:-1]]
        
        # Calculamos min y max de forma segmentada
        starts = boundaries[:-1]
        mins = np.minimum.reduceat(sorted_points, starts)
        maxs = np.maximum.reduceat(sorted_points, starts)

        for i, key_arr in enumerate(unique_keys):
            key = tuple(key_arr)
            start, end = boundaries[i], boundaries[i+1]
            
            chunk_data[key] = sorted_points[start:end]
            chunk_bounds[key] = (mins[i], maxs[i])

        return chunk_data, chunk_bounds
    
    def make_cube_geometry(self):
        s = self.cube_size

        faces = np.array([
            # FRONT (0,0,1)
            [-s,-s, s],[ s,-s, s],[ s, s, s],  [-s,-s, s],[ s, s, s],[-s, s, s],

            # BACK (0,0,-1)
            [-s,-s,-s],[-s, s,-s],[ s, s,-s],  [-s,-s,-s],[ s, s,-s],[ s,-s,-s],

            # LEFT (-1,0,0)
            [-s,-s,-s],[-s,-s, s],[-s, s, s],  [-s,-s,-s],[-s, s, s],[-s, s,-s],

            # RIGHT (1,0,0)
            [ s,-s,-s],[ s, s,-s],[ s, s, s],  [ s,-s,-s],[ s, s, s],[ s,-s, s],

            # TOP (0,1,0)
            [-s, s,-s],[-s, s, s],[ s, s, s],  [-s, s,-s],[ s, s, s],[ s, s,-s],

            # BOTTOM (0,-1,0)
            [-s,-s,-s],[ s,-s,-s],[ s,-s, s],  [-s,-s,-s],[ s,-s, s],[-s,-s, s],
        ], dtype=np.float32)

        # normales por cara (6 vértices por cara)
        normals = np.array([
            [0,0,1]]*6 +
            [[0,0,-1]]*6 +
            [[-1,0,0]]*6 +
            [[1,0,0]]*6 +
            [[0,1,0]]*6 +
            [[0,-1,0]]*6,
            dtype=np.float32
        )

        face_flags = np.zeros(len(faces), dtype=np.float32)

        edges = np.array([
            [-s,-s,-s],[ s,-s,-s], [ s,-s,-s],[ s, s,-s],
            [ s, s,-s],[-s, s,-s], [-s, s,-s],[-s,-s,-s],
            [-s,-s, s],[ s,-s, s], [ s,-s, s],[ s, s, s],
            [ s, s, s],[-s, s, s], [-s, s, s],[-s,-s, s],
            [-s,-s,-s],[-s,-s, s], [ s,-s,-s],[ s,-s, s],
            [ s, s,-s],[ s, s, s], [-s, s,-s],[-s, s, s],
        ], dtype=np.float32)

        edge_flags = np.ones(len(edges), dtype=np.float32)

        return faces, normals, face_flags, edges, edge_flags

    def macos_3d_render(self):
        import glfw
        import ctypes
        import Metal        # pyobjc-framework-Metal
        import Cocoa        # pyobjc-framework-Cocoa
        import objc
        from Foundation import NSAutoreleasePool

        # Shader MSL (Metal Shading Language)
        MSL_SHADER = """
    #include <metal_stdlib>
    using namespace metal;

    struct Uniforms { float4x4 mvp; };

    struct VertIn {
        float3 vert   [[attribute(0)]];
        float  edge   [[attribute(1)]];
        float3 offset [[attribute(2)]];
    };

    struct VertOut {
        float4 pos  [[position]];
        float  edge;
    };

    vertex VertOut vert_main(VertIn in [[stage_in]],
                            constant Uniforms &u [[buffer(2)]]) {
        VertOut out;
        out.pos  = u.mvp * float4(in.vert + in.offset, 1.0);
        out.edge = in.edge;
        return out;
    }

    fragment float4 frag_main(VertOut in [[stage_in]]) {
        return (in.edge > 0.5)
            ? float4(0, 1, 0, 1)   // aristas verdes
            : float4(1, 1, 1, 1);  // caras blancas
    }
    """

        # ── Init glfw ──────────────────────────────────────────────────────────
        if not glfw.init():
            raise RuntimeError("glfw.init() falló")
        glfw.window_hint(glfw.CLIENT_API, glfw.NO_API)   # sin OpenGL
        window = glfw.create_window(width, height,
            f"Game of Life 3D [Metal {'Apple Silicon' if IS_SILICON else 'macOS'}]",
            None, None)
        if not window:
            glfw.terminate()
            raise RuntimeError("No se pudo crear la ventana glfw")

        # ── Obtener MTLDevice (GPU) ─────────────────────────────────────────────
        pool    = NSAutoreleasePool.alloc().init()
        devices = Metal.MTLCopyAllDevices()
        device  = devices[0]
        print(f"[Metal] GPU: {device.name()}")

        # ── CAMetalLayer (surface de presentación) ─────────────────────────────
        # Obtener NSWindow desde glfw y añadir una CAMetalLayer
        from ctypes import cdll, c_void_p
        glfw_lib  = cdll.LoadLibrary(glfw.get_cocoa_library_path() if hasattr(glfw, 'get_cocoa_library_path') else 'libglfw.3.dylib')
        ns_window = c_void_p(glfw.get_cocoa_window(window))

        layer = Metal.CAMetalLayer.layer()
        layer.setDevice_(device)
        pixel_fmt = Metal.MTLPixelFormatBGRA8Unorm
        layer.setPixelFormat_(pixel_fmt)
        layer.setFramebufferOnly_(True)

        # Asociar la layer a la ventana vía ObjC runtime
        ns_view = objc.objc_object(c_void_p=ns_window.value)
        try:
            content_view = ns_view.contentView()
            content_view.setLayer_(layer)
            content_view.setWantsLayer_(True)
        except Exception as e:
            print(f"[Metal] Advertencia al configurar layer: {e}")

        # ── Compilar shaders ───────────────────────────────────────────────────
        err    = objc.nil
        lib, err = device.newLibraryWithSource_options_error_(MSL_SHADER, None, None)
        if lib is None:
            raise RuntimeError(f"Error compilando shaders MSL: {err}")
        vert_fn = lib.newFunctionWithName_("vert_main")
        frag_fn = lib.newFunctionWithName_("frag_main")
        print("[Metal] Shaders MSL compilados OK")

        # ── Vertex descriptor ──────────────────────────────────────────────────
        # pyobjc: usar objectAtIndexedSubscript_ en lugar de [] y set* en lugar de *_
        vdesc = Metal.MTLVertexDescriptor.vertexDescriptor()
        a = vdesc.attributes().objectAtIndexedSubscript_
        l = vdesc.layouts().objectAtIndexedSubscript_

        # attr 0: vert  (float3, offset 0,  buffer 0, per-vertex)
        a(0).setFormat_(Metal.MTLVertexFormatFloat3)
        a(0).setOffset_(0)
        a(0).setBufferIndex_(0)
        # attr 1: edge  (float,  offset 12, buffer 0, per-vertex)
        a(1).setFormat_(Metal.MTLVertexFormatFloat)
        a(1).setOffset_(12)
        a(1).setBufferIndex_(0)
        # attr 2: offset (float3, offset 0, buffer 1, per-instance)
        a(2).setFormat_(Metal.MTLVertexFormatFloat3)
        a(2).setOffset_(0)
        a(2).setBufferIndex_(1)
        # layouts
        l(0).setStride_(16)
        l(0).setStepFunction_(Metal.MTLVertexStepFunctionPerVertex)
        l(1).setStride_(12)
        l(1).setStepFunction_(Metal.MTLVertexStepFunctionPerInstance)
        # ── Depth stencil ──────────────────────────────────────────────────────
        depth_fmt  = Metal.MTLPixelFormatDepth32Float
        ds_desc    = Metal.MTLDepthStencilDescriptor.alloc().init()
        ds_desc.setDepthCompareFunction_(Metal.MTLCompareFunctionLess)
        ds_desc.setDepthWriteEnabled_(True)
        depth_state = device.newDepthStencilStateWithDescriptor_(ds_desc)

        depth_tex = None
        def make_depth_tex(w, h):
            td = Metal.MTLTextureDescriptor.texture2DDescriptorWithPixelFormat_width_height_mipmapped_(
                depth_fmt, w, h, False)
            td.setUsage_(Metal.MTLTextureUsageRenderTarget)
            td.setStorageMode_(Metal.MTLStorageModePrivate)
            return device.newTextureWithDescriptor_(td)
        depth_tex = make_depth_tex(self.width, self.height)

        # ── Render pipeline ────────────────────────────────────────────────────
        def make_pipeline(primitive_topology=None):
            pd = Metal.MTLRenderPipelineDescriptor.alloc().init()
            pd.setVertexFunction_(vert_fn)
            pd.setFragmentFunction_(frag_fn)
            pd.setVertexDescriptor_(vdesc)
            pd.colorAttachments().objectAtIndexedSubscript_(0).setPixelFormat_(pixel_fmt)
            pd.setDepthAttachmentPixelFormat_(depth_fmt)
            pipe, err = device.newRenderPipelineStateWithDescriptor_error_(pd, None)
            if pipe is None:
                raise RuntimeError(f"Pipeline error: {err}")
            return pipe

        pipeline = make_pipeline()
        cmd_queue = device.newCommandQueue()

        # ── Geometría ──────────────────────────────────────────────────────────
        faces, normals, face_flags, edges, edge_flags = self.make_cube_geometry()

        def interleave(verts, flags):
            return np.column_stack([verts, flags]).astype(np.float32)

        face_data  = interleave(faces, face_flags)
        edge_data  = interleave(edges, edge_flags)

        def make_buf(data):
            arr = np.ascontiguousarray(data, dtype=np.float32)
            return device.newBufferWithBytes_length_options_(
                arr.tobytes(), arr.nbytes, Metal.MTLResourceStorageModeShared)

        vbuf_faces   = make_buf(face_data)
        vbuf_edges   = make_buf(edge_data)
        offsets_buf  = make_buf(all_points)
        # uniform_buf se crea cada frame con newBufferWithBytes_length_options_

        n_fv = len(face_data)
        n_ev = len(edge_data)

        # ── Estado mutable ─────────────────────────────────────────────────────
        S = {"rx": 0.0, "ry": 0.0, "dist": self.base_dist,
            "last_scroll_y": 0.0, "w": self.width, "h": self.height}

        def scroll_cb(win, dx, dy):
            speed = max(1.0, S["dist"] * 0.05)
            S["dist"] = max(self.zoom_min, S["dist"] - dy * speed)

        glfw.set_scroll_callback(window, scroll_cb)

        print(f"[Metal] Renderizando {self.N} instancias | Controles: flechas=rotar  scroll=zoom  R=reset")

        while not glfw.window_should_close(window):
            glfw.poll_events()

            # Teclado
            def key(k): return glfw.get_key(window, k) == glfw.PRESS
            if key(glfw.KEY_LEFT):  S["ry"] += 1
            if key(glfw.KEY_RIGHT): S["ry"] -= 1
            if key(glfw.KEY_UP):    S["rx"] -= 1
            if key(glfw.KEY_DOWN):  S["rx"] += 1
            if key(glfw.KEY_EQUAL) or key(glfw.KEY_KP_ADD):
                S["dist"] = max(self.zoom_min, S["dist"] - max(1.0, S["dist"] * 0.02))
            if key(glfw.KEY_MINUS) or key(glfw.KEY_KP_SUBTRACT):
                S["dist"] += max(1.0, S["dist"] * 0.02)
            if key(glfw.KEY_R):
                S["rx"] = S["ry"] = 0.0; S["dist"] = self.base_dist

            # MVP → uniform buffer
            mvp = self.compute_mvp(S["rx"], S["ry"], S["dist"])
            mvp_bytes = mvp.T.astype(np.float32).tobytes()
            # Crear buffer de uniforms con los bytes directamente (más simple y confiable)
            uniform_buf = device.newBufferWithBytes_length_options_(
                mvp_bytes, 64, Metal.MTLResourceStorageModeShared)

            # Obtener drawable de la CAMetalLayer
            drawable = layer.nextDrawable()
            if drawable is None:
                continue

            # Resize depth si cambia el tamaño
            fw, fh = glfw.get_framebuffer_size(window)
            if (fw, fh) != (S["w"], S["h"]):
                depth_tex = make_depth_tex(fw, fh)
                layer.setDrawableSize_((fw, fh))
                S["w"], S["h"] = fw, fh

            # Render pass descriptor
            rpd = Metal.MTLRenderPassDescriptor.renderPassDescriptor()
            rpd.colorAttachments().objectAtIndexedSubscript_(0).setTexture_(drawable.texture())
            rpd.colorAttachments().objectAtIndexedSubscript_(0).setLoadAction_(Metal.MTLLoadActionClear)
            rpd.colorAttachments().objectAtIndexedSubscript_(0).setClearColor_(Metal.MTLClearColorMake(0.05, 0.05, 0.1, 1.0))
            rpd.colorAttachments().objectAtIndexedSubscript_(0).setStoreAction_(Metal.MTLStoreActionStore)
            rpd.depthAttachment().setTexture_(depth_tex)
            rpd.depthAttachment().setLoadAction_(Metal.MTLLoadActionClear)
            rpd.depthAttachment().setClearDepth_(1.0)
            rpd.depthAttachment().setStoreAction_(Metal.MTLStoreActionDontCare)

            cmd_buf = cmd_queue.commandBuffer()
            enc     = cmd_buf.renderCommandEncoderWithDescriptor_(rpd)

            enc.setRenderPipelineState_(pipeline)
            enc.setDepthStencilState_(depth_state)
            enc.setVertexBuffer_offset_atIndex_(uniform_buf, 0, 2)  # uniforms en buffer(2)

            # Caras
            enc.setVertexBuffer_offset_atIndex_(vbuf_faces, 0, 0)
            enc.setVertexBuffer_offset_atIndex_(offsets_buf, 0, 1)
            enc.drawPrimitives_vertexStart_vertexCount_instanceCount_(
                Metal.MTLPrimitiveTypeTriangle, 0, n_fv, self.N)

            # Aristas
            enc.setVertexBuffer_offset_atIndex_(vbuf_edges, 0, 0)
            enc.setVertexBuffer_offset_atIndex_(offsets_buf, 0, 1)
            enc.drawPrimitives_vertexStart_vertexCount_instanceCount_(
                Metal.MTLPrimitiveTypeLine, 0, n_ev, self.N)

            enc.endEncoding()
            cmd_buf.presentDrawable_(drawable)
            cmd_buf.commit()

        glfw.destroy_window(window)
        glfw.terminate()
        del pool

    def open_gl_render(self):
            import pygame
            from pygame.locals import DOUBLEBUF, OPENGL
            from OpenGL.GL import (
                GL_VERSION, GL_DEPTH_TEST,
                GL_COLOR_BUFFER_BIT, GL_DEPTH_BUFFER_BIT,
                GL_ARRAY_BUFFER, GL_STATIC_DRAW,
                GL_FLOAT, GL_FALSE, GL_TRIANGLES, GL_LINES,
                glGetString, glEnable, glViewport,
                glClearColor, glClear, glUseProgram,
                glGenVertexArrays, glBindVertexArray,
                glGenBuffers, glBindBuffer, glBufferData,
                glEnableVertexAttribArray,
                glVertexAttribPointer, glVertexAttribDivisor,
                glDrawArraysInstanced,
                glGetUniformLocation, glUniformMatrix4fv,
                GL_VERTEX_SHADER, GL_FRAGMENT_SHADER, GL_COMPILE_STATUS, GL_LINK_STATUS,
                glCreateShader, glShaderSource, glCompileShader,
                glGetShaderiv, glGetShaderInfoLog, glDeleteShader,
                glCreateProgram, glAttachShader, glLinkProgram,
                glGetProgramiv, glGetProgramInfoLog, GL_DYNAMIC_DRAW,
                GL_CULL_FACE, GL_BACK, glCullFace, glBufferSubData
            )

            VERT_GLSL = """
        #version 410 core

        layout(location=0) in vec3  in_vert;
        layout(location=1) in float in_edge;
        layout(location=2) in vec3  in_offset;
        layout(location=3) in vec3  in_normal;

        uniform mat4 mvp;

        out float v_edge;
        out vec3 v_normal;

        void main() {
            // posición del centro del cubo en clip space
            vec4 center = mvp * vec4(in_offset, 1.0);

            if (abs(center.x) > center.w ||
                abs(center.y) > center.w ||
                abs(center.z) > center.w) {
                gl_Position = vec4(2.0, 2.0, 2.0, 1.0);
                return;
            }

            // posición final del vértice
            gl_Position = mvp * vec4(in_vert + in_offset, 1.0);

            v_edge = in_edge;
            v_normal = in_normal;
        }
        """

            FRAG_GLSL = """
        #version 410 core
        in  float v_edge;
        in vec3 v_normal;
        out vec4  fragColor;
        void main() {
            vec3 light_dir = normalize(vec3(0.0, 0.0, 1.0)); // dirección de luz
            float diff = max(dot(normalize(v_normal), light_dir), 0.2);

            vec3 baseColor = (v_edge > 0.5)
                ? vec3(0.2, 0.2, 0.8)   // bordes
                : vec3(1.0, 1.0, 1.0);  // caras

            vec3 color = baseColor * diff;

            fragColor = vec4(color, 1.0);
        }
        """

            def compile_shader(src, kind):
                sh = glCreateShader(kind)
                glShaderSource(sh, src)
                glCompileShader(sh)
                if not glGetShaderiv(sh, GL_COMPILE_STATUS):
                    raise RuntimeError(glGetShaderInfoLog(sh).decode())
                return sh

            def link_prog(vs_src, fs_src):
                vs = compile_shader(vs_src, GL_VERTEX_SHADER)
                fs = compile_shader(fs_src, GL_FRAGMENT_SHADER)
                p  = glCreateProgram()
                glAttachShader(p, vs); glAttachShader(p, fs)
                glLinkProgram(p)
                glDeleteShader(vs); glDeleteShader(fs)
                if not glGetProgramiv(p, GL_LINK_STATUS):
                    raise RuntimeError(glGetProgramInfoLog(p).decode())
                return p

            pygame.init()
            display = (self.width, self.height)
            pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 4)
            pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 1)
            pygame.display.gl_set_attribute(pygame.GL_CONTEXT_PROFILE_MASK,
                                            pygame.GL_CONTEXT_PROFILE_CORE)
            pygame.display.gl_set_attribute(pygame.GL_CONTEXT_FORWARD_COMPATIBLE_FLAG, True)
            pygame.display.set_mode(display, DOUBLEBUF | OPENGL)
            pygame.display.set_caption("Renderizado 3D - OpenGL")

            print(f"[OpenGL] {glGetString(GL_VERSION).decode()}")
            glViewport(0, 0, *display)

            prog = link_prog(VERT_GLSL, FRAG_GLSL)
            glUseProgram(prog)
            mvp_loc = glGetUniformLocation(prog, "mvp")

            faces, normals, face_flags, edges, edge_flags = self.make_cube_geometry()

            def build_vao(verts, flags, normals):
                vao = glGenVertexArrays(1)
                glBindVertexArray(vao)

                for loc, data, n_comp in [
                    (0, verts, 3),
                    (1, flags[:,None] if flags.ndim==1 else flags, 1),
                    (3, normals, 3),
                ]:
                    vbo = glGenBuffers(1)
                    glBindBuffer(GL_ARRAY_BUFFER, vbo)
                    flat = data.astype(np.float32)
                    glBufferData(GL_ARRAY_BUFFER, flat.nbytes, flat, GL_STATIC_DRAW)
                    glEnableVertexAttribArray(loc)
                    glVertexAttribPointer(loc, n_comp, GL_FLOAT, GL_FALSE, 0, None)

                glBindVertexArray(0)
                return vao, len(verts)

            vao_f, n_fv = build_vao(faces, face_flags, normals)
            vao_e, n_ev = build_vao(edges, edge_flags, normals)

            CHUNK_SIZE = 16

            chunk_data, chunk_bounds = self.get_chunks()

            chunk_vbos = {}

            for key, pts in chunk_data.items():
                vbo = glGenBuffers(1)
                glBindBuffer(GL_ARRAY_BUFFER, vbo)
                glBufferData(GL_ARRAY_BUFFER, pts.nbytes, pts, GL_STATIC_DRAW)
                chunk_vbos[key] = (vbo, len(pts))

            print(f"[Chunks] Total: {len(chunk_data)} | Ejemplo: {list(chunk_data.keys())[:5]}")

            glEnable(GL_DEPTH_TEST)
            glEnable(GL_CULL_FACE)
            glCullFace(GL_BACK)
            rx = ry = 0.0
            cam_x, cam_y, cam_z = 0.0, 0.0, 0.0
            mouse_down = False
            sensitivity = 0.2
            dist  = self.base_dist
            clock = pygame.time.Clock()
            running = True

            while running:
                for e in pygame.event.get():
                    if e.type == pygame.QUIT:
                        running = False
                    elif e.type == pygame.MOUSEBUTTONDOWN:
                        if e.button == 1:  # click izquierdo
                            mouse_down = True

                    elif e.type == pygame.MOUSEBUTTONUP:
                        if e.button == 1:
                            mouse_down = False

                    elif e.type == pygame.MOUSEMOTION:
                        if mouse_down:
                            dx, dy = e.rel
                            ry += dx * sensitivity
                            rx += dy * sensitivity

                    elif e.type == pygame.MOUSEWHEEL:
                        speed = max(1.0, dist * 0.05)
                        dist -= e.y * speed
                        dist  = max(self.zoom_min, dist)
                        
                    elif e.type == pygame.KEYDOWN:
                        if e.key == pygame.K_r:
                            rx = ry = 0.0; dist = self.base_dist; cam_x = cam_y = cam_z = 0.0

                keys = pygame.key.get_pressed()
                speed = 1.0
                if keys[pygame.K_LEFT]:  cam_x -= speed
                if keys[pygame.K_RIGHT]: cam_x += speed
                if keys[pygame.K_UP]:    cam_y += speed
                if keys[pygame.K_DOWN]:  cam_y -= speed
                if keys[pygame.K_EQUALS] or keys[pygame.K_PLUS]:
                    dist = max(self.zoom_min, dist - max(1.0, dist * 0.1))
                if keys[pygame.K_MINUS]:
                    dist += max(1.0, dist * 0.1)

                mvp = self.compute_mvp(rx, ry, dist, cam_x, cam_y, cam_z)
                #print(f"Cam pos: ({cam_x:.1f}, {cam_y:.1f}, {cam_z:.1f})  |  Dist: {dist:.1f}  |  Rot: ({rx:.1f}, {ry:.1f})  |  Instancias: {N}")
                glClearColor(0.05, 0.05, 0.1, 1.0)
                glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

                glUseProgram(prog)
                #print("MVP:\n", mvp)

                planes = self.extract_frustum_planes(mvp)
                #print(f"Frustum planes: {len(planes)}")

                visible_chunks = []

                for key, (min_p, max_p) in chunk_bounds.items():
                    if self.aabb_in_frustum_minmax(planes, min_p, max_p):
                        visible_chunks.append(key)
                    
                #print(f"Chunks visibles: {len(visible_chunks)} / {len(chunk_bounds)}")

                glUniformMatrix4fv(mvp_loc, 1, GL_FALSE, mvp.T)

                visible_pts = []

                for key in visible_chunks:
                    pts = chunk_data[key]
                    visible_pts.append(pts)

                if len(visible_pts) == 0:
                    continue

                visible_pts = np.concatenate(visible_pts, axis=0)
                visible_N = len(visible_pts)

                max_points = len(self.all_points)

                offset_vbo = glGenBuffers(1)
                glBindBuffer(GL_ARRAY_BUFFER, offset_vbo)
                glBufferData(GL_ARRAY_BUFFER,
                            max_points * 3 * 4,
                            None,
                            GL_DYNAMIC_DRAW)
                
                glBindBuffer(GL_ARRAY_BUFFER, offset_vbo)
                glBufferSubData(GL_ARRAY_BUFFER, 0, visible_pts.nbytes, visible_pts)

                glBindVertexArray(vao_f)

                glEnableVertexAttribArray(2)
                glVertexAttribPointer(2, 3, GL_FLOAT, GL_FALSE, 0, None)
                glVertexAttribDivisor(2, 1)

                glDrawArraysInstanced(GL_TRIANGLES, 0, n_fv, visible_N)

                glBindVertexArray(vao_e)

                glEnableVertexAttribArray(2)
                glVertexAttribPointer(2, 3, GL_FLOAT, GL_FALSE, 0, None)
                glVertexAttribDivisor(2, 1)

                glDrawArraysInstanced(GL_LINES, 0, n_ev, visible_N)
                glBindVertexArray(0)

                #print("-" * 60)

                pygame.display.flip()
                clock.tick(60)

            pygame.quit()