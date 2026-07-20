

import platform
import os
import sys
import threading
import numpy as np
from core import config
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
        print(f"[Sim] Generations: {self.generations}, Living cells: {self.N}")
    
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

    def compute_mvp(self, cam_x, cam_y, cam_z, yaw, pitch):
        """Corrected and more stable free camera"""
        
        proj = self.perspective(45, self.width / self.height, 0.1, 2000.0)
        
        # Direction vectors
        cy = np.cos(np.radians(yaw))
        sy = np.sin(np.radians(yaw))
        cp = np.cos(np.radians(pitch))
        sp = np.sin(np.radians(pitch))
        
        forward = np.array([cy * cp, sp, sy * cp], dtype=np.float32)
        right = np.cross(forward, np.array([0, 1, 0], dtype=np.float32))
        right /= np.linalg.norm(right)
        up = np.cross(right, forward)
        
        pos = np.array([cam_x, cam_y, cam_z], dtype=np.float32)
        
        # View Matrix (correct row-major construction for NumPy)
        view = np.eye(4, dtype=np.float32)
        view[0, 0:3] = right
        view[1, 0:3] = up
        view[2, 0:3] = -forward
        
        view[0, 3] = -np.dot(right, pos)
        view[1, 3] = -np.dot(up, pos)
        # IMPORTANT: Since Z basis is -forward, the dot product is positive
        view[2, 3] = np.dot(forward, pos)
        
        # Model (Identity)
        # Cells are already positioned in the world (in.offset).
        # Translating them again by (CX, CY, CZ) would push them out of the camera's visual range.
        model = np.eye(4, dtype=np.float32)
        
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
            print("Warning: incomplete frustum:", len(planes))
        return out

    def aabb_in_frustum_minmax(self, planes, min_p, max_p):
        for p in planes:
            n = p[:3]
            d = p[3]

            # select extreme vertex directly
            p_vertex = np.where(n > 0, max_p, min_p)

            if np.dot(n, p_vertex) + d < 0:
                return False

        return True

    def get_chunks(self):
        # Calculate chunk coordinates in vectorized form
        all_points = np.asarray(self.all_points)
        coords = (all_points // self.chunk_size).astype(np.int32)

        # Sort points by their chunk coordinates (lexicographically)
        sort_idx = np.lexsort((coords[:, 2], coords[:, 1], coords[:, 0]))
        sorted_points = all_points[sort_idx]
        sorted_coords = coords[sort_idx]

        # Find boundaries where one chunk changes to another
        diffs = np.any(np.diff(sorted_coords, axis=0) != 0, axis=1)
        # Get the start indices of each block
        boundaries = np.concatenate(([0], np.where(diffs)[0] + 1, [len(sorted_points)]))

        chunk_data = {}
        chunk_bounds = {}

        # Extract data using 'reduceat' for mins and maxes
        unique_keys = sorted_coords[boundaries[:-1]]
        
        # Calculate min and max in segmented form
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

        # normals per face (6 vertices per face)
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
        print(f"[Metal 3D] Iniciando render desde PID = {os.getpid()}")
        import glfw
        import ctypes
        import Metal
        import objc
        from Foundation import NSAutoreleasePool
        # Render distance
        visible_generations = 100
        MSL_SHADER = """
        #include <metal_stdlib>
        using namespace metal;
        struct Uniforms { float4x4 mvp; };
        struct VertIn {
            float3 vert [[attribute(0)]];
            float edge [[attribute(1)]];
            float3 offset [[attribute(2)]];
        };
        struct VertOut {
            float4 pos [[position]];
            float edge;
        };
        vertex VertOut vert_main(VertIn in [[stage_in]], constant Uniforms &u [[buffer(2)]]) {
            VertOut out;
            out.pos = u.mvp * float4(in.vert + in.offset, 1.0);
            out.edge = in.edge;
            return out;
        }
        fragment float4 frag_main(VertOut in [[stage_in]]) {    
            
            float4 color_arista = float4(0.0, 0.0, 1.0, 1.0);
            
            float4 color_cara = float4(1.0, 1.0, 1.0, 1.0);
            
            return (in.edge > 0.5) ? color_arista : color_cara;
        }
        """

        if not glfw.init():
            raise RuntimeError("glfw.init() failed")
        glfw.window_hint(glfw.CLIENT_API, glfw.NO_API)
        window = glfw.create_window(self.width, self.height, f"Game of Life 3D [Metal]", None, None)
        if not window:
            glfw.terminate()
            raise RuntimeError("No window")

        pool = NSAutoreleasePool.alloc().init()
        devices = Metal.MTLCopyAllDevices()
        device = next((d for d in devices if "radeon" in d.name().lower() or "amd" in d.name().lower()), devices[0])
        print(device)

        # Layer setup (igual)
        from ctypes import cdll, c_void_p
        glfw_lib = cdll.LoadLibrary(glfw.get_cocoa_library_path() if hasattr(glfw, 'get_cocoa_library_path') else 'libglfw.3.dylib')
        ns_window = c_void_p(glfw.get_cocoa_window(window))
        layer = Metal.CAMetalLayer.layer()
        layer.setDevice_(device)
        pixel_fmt = Metal.MTLPixelFormatBGRA8Unorm
        layer.setPixelFormat_(pixel_fmt)
        layer.setFramebufferOnly_(True)
        ns_view = objc.objc_object(c_void_p=ns_window.value)
        try:
            ns_view.contentView().setLayer_(layer)
            ns_view.contentView().setWantsLayer_(True)
        except:
            pass

        # Pipeline y buffers (simplificado)
        lib, _ = device.newLibraryWithSource_options_error_(MSL_SHADER, None, None)
        vert_fn = lib.newFunctionWithName_("vert_main")
        frag_fn = lib.newFunctionWithName_("frag_main")

        vdesc = Metal.MTLVertexDescriptor.vertexDescriptor()
        a = vdesc.attributes().objectAtIndexedSubscript_
        l = vdesc.layouts().objectAtIndexedSubscript_
        a(0).setFormat_(Metal.MTLVertexFormatFloat3); a(0).setOffset_(0); a(0).setBufferIndex_(0)
        a(1).setFormat_(Metal.MTLVertexFormatFloat); a(1).setOffset_(12); a(1).setBufferIndex_(0)
        a(2).setFormat_(Metal.MTLVertexFormatFloat3); a(2).setOffset_(0); a(2).setBufferIndex_(1)
        l(0).setStride_(16); l(0).setStepFunction_(Metal.MTLVertexStepFunctionPerVertex)
        l(1).setStride_(12); l(1).setStepFunction_(Metal.MTLVertexStepFunctionPerInstance)

        depth_fmt = Metal.MTLPixelFormatDepth32Float
        ds_desc = Metal.MTLDepthStencilDescriptor.alloc().init()
        ds_desc.setDepthCompareFunction_(Metal.MTLCompareFunctionLess)
        ds_desc.setDepthWriteEnabled_(True)
        depth_state = device.newDepthStencilStateWithDescriptor_(ds_desc)

        pd = Metal.MTLRenderPipelineDescriptor.alloc().init()
        pd.setVertexFunction_(vert_fn)
        pd.setFragmentFunction_(frag_fn)
        pd.setVertexDescriptor_(vdesc)
        pd.colorAttachments().objectAtIndexedSubscript_(0).setPixelFormat_(pixel_fmt)
        pd.setDepthAttachmentPixelFormat_(depth_fmt)
        pipeline, _ = device.newRenderPipelineStateWithDescriptor_error_(pd, None)
        self.pipeline = pipeline
        self.depth_state = depth_state

        # Geometry
        faces, _, face_flags, edges, edge_flags = self.make_cube_geometry()
        def interleave(verts, flags):
            return np.column_stack([verts, flags]).astype(np.float32)
        face_data = interleave(faces, face_flags)
        edge_data = interleave(edges, edge_flags)

        def make_buf(data):
            arr = np.ascontiguousarray(data, dtype=np.float32)
            return device.newBufferWithBytes_length_options_(arr.tobytes(), arr.nbytes, Metal.MTLResourceStorageModeShared)

        vbuf_faces = make_buf(face_data)
        vbuf_edges = make_buf(edge_data)
        offsets_buf = make_buf(self.all_points)

        uniform_buffers = [device.newBufferWithLength_options_(64, Metal.MTLResourceStorageModeShared) for _ in range(3)]
        current_uniform_idx = 0
        n_fv = len(face_data)
        n_ev = len(edge_data)

        # Safer initial camera
        cam = {"x": self.CX, "y": self.CY + 10, "z": self.CZ + 80, "yaw": -90, "pitch": -20, "speed": 1.2}
        S = {"w": self.width, "h": self.height, "dirty": True}
        self.last_generation = getattr(self, 'generation', 0)
        self.depth_tex = None

        cmd_queue = device.newCommandQueue()
        print(f"[DEBUG] Centrado en ({self.CX:.1f}, {self.CY:.1f}, {self.CZ:.1f}) | Celdas: {self.N}")

        def update_metal_buffer(metal_buf, np_array):
            data_bytes = np_array.tobytes()
            # PyObjC envuelve el void* en un objc.varlist.
            # .as_buffer(size) nos da acceso directo a esa memoria en C para sobreescribirla.
            metal_buf.contents().as_buffer(len(data_bytes))[:] = data_bytes

        # Make sure to define this BEFORE the while if you haven't
        # visible_generations = 50 

        while not glfw.window_should_close(window):
            glfw.poll_events()

            def key(k): return glfw.get_key(window, k) == glfw.PRESS
            moved = False

            if key(glfw.KEY_W): cam["x"] += cam["speed"]*np.cos(np.radians(cam["yaw"])); cam["z"] += cam["speed"]*np.sin(np.radians(cam["yaw"])); moved=True
            if key(glfw.KEY_S): cam["x"] -= cam["speed"]*np.cos(np.radians(cam["yaw"])); cam["z"] -= cam["speed"]*np.sin(np.radians(cam["yaw"])); moved=True
            if key(glfw.KEY_A): cam["x"] += cam["speed"]*np.cos(np.radians(cam["yaw"]-90)); cam["z"] += cam["speed"]*np.sin(np.radians(cam["yaw"]-90)); moved=True
            if key(glfw.KEY_D): cam["x"] += cam["speed"]*np.cos(np.radians(cam["yaw"]+90)); cam["z"] += cam["speed"]*np.sin(np.radians(cam["yaw"]+90)); moved=True
            if key(glfw.KEY_SPACE): cam["y"] += cam["speed"]; moved = True
            if key(glfw.KEY_LEFT_SHIFT): cam["y"] -= cam["speed"]; moved = True

            if key(glfw.KEY_LEFT): cam["yaw"] -= 3; moved = True
            if key(glfw.KEY_RIGHT): cam["yaw"] += 3; moved = True
            if key(glfw.KEY_UP): cam["pitch"] = min(89, cam["pitch"] + 3); moved = True
            if key(glfw.KEY_DOWN): cam["pitch"] = max(-89, cam["pitch"] - 3); moved = True
            
            if key(glfw.KEY_R):
                cam["x"] = self.CX
                cam["y"] = self.CY + 10
                cam["z"] = self.CZ + 80
                cam["yaw"] = -90
                cam["pitch"] = -20
                moved = True
                
            if key(glfw.KEY_O) or key(glfw.KEY_KP_ADD): 
                visible_generations = min(1000, visible_generations + 2)
                moved = True
            if key(glfw.KEY_I) or key(glfw.KEY_KP_SUBTRACT): 
                visible_generations = max(5, visible_generations - 2)
                moved = True

            # MVP
            mvp = self.compute_mvp(cam["x"], cam["y"], cam["z"], cam["yaw"], cam["pitch"])

            # --- FILTRADO DE DISTANCIA (CULLING) ---
            dist_z = np.abs(self.all_points[:, 2] - cam["z"])
            mask = dist_z <= visible_generations
            visible_points = self.all_points[mask]
            
            # Obtenemos la nueva cantidad de instancias a dibujar
            instance_count = len(visible_points)

            # Actualizamos el buffer SOLO con los puntos visibles
            if instance_count > 0:
                update_metal_buffer(offsets_buf, visible_points.astype(np.float32))

            # --- UNIFORM UPDATE (Matrix) ---
            uniform_buf = uniform_buffers[current_uniform_idx]
            update_metal_buffer(uniform_buf, mvp.T.astype(np.float32))
            current_uniform_idx = (current_uniform_idx + 1) % 3

            # --- RENDER PASS ---
            drawable = layer.nextDrawable()
            if not drawable: 
                continue

            fw, fh = glfw.get_framebuffer_size(window)
            if self.depth_tex is None or (fw, fh) != (S["w"], S["h"]):
                td = Metal.MTLTextureDescriptor.texture2DDescriptorWithPixelFormat_width_height_mipmapped_(depth_fmt, fw, fh, False)
                td.setUsage_(Metal.MTLTextureUsageRenderTarget)
                td.setStorageMode_(Metal.MTLStorageModePrivate)
                self.depth_tex = device.newTextureWithDescriptor_(td)
                layer.setDrawableSize_((fw, fh))
                S["w"], S["h"] = fw, fh
            
            rpd = Metal.MTLRenderPassDescriptor.renderPassDescriptor()
            color_att = rpd.colorAttachments().objectAtIndexedSubscript_(0)
            color_att.setTexture_(drawable.texture())
            color_att.setLoadAction_(Metal.MTLLoadActionClear)
            # Dark blue to confirm Metal is clearing the frame
            color_att.setClearColor_(Metal.MTLClearColorMake(0.1, 0.1, 0.2, 1.0)) 
            color_att.setStoreAction_(Metal.MTLStoreActionStore)

            rpd.depthAttachment().setTexture_(self.depth_tex)
            rpd.depthAttachment().setLoadAction_(Metal.MTLLoadActionClear)
            rpd.depthAttachment().setClearDepth_(1.0)
            rpd.depthAttachment().setStoreAction_(Metal.MTLStoreActionDontCare)

            cmd_buf = cmd_queue.commandBuffer()
            enc = cmd_buf.renderCommandEncoderWithDescriptor_(rpd)
            enc.setRenderPipelineState_(self.pipeline)
            enc.setDepthStencilState_(self.depth_state)
            
            # Dibujado
            enc.setVertexBuffer_offset_atIndex_(uniform_buf, 0, 2)

            if instance_count > 0:
                # Caras
                enc.setVertexBuffer_offset_atIndex_(vbuf_faces, 0, 0)
                enc.setVertexBuffer_offset_atIndex_(offsets_buf, 0, 1)
                enc.drawPrimitives_vertexStart_vertexCount_instanceCount_(Metal.MTLPrimitiveTypeTriangle, 0, n_fv, instance_count)

                # Bordes
                enc.setVertexBuffer_offset_atIndex_(vbuf_edges, 0, 0)
                enc.setVertexBuffer_offset_atIndex_(offsets_buf, 0, 1)
                enc.drawPrimitives_vertexStart_vertexCount_instanceCount_(Metal.MTLPrimitiveTypeLine, 0, n_ev, instance_count)

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
                GL_ARRAY_BUFFER, GL_STATIC_DRAW, GL_UNIFORM_BUFFER,
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
            // center of the cube in clip space
            vec4 center = mvp * vec4(in_offset, 1.0);

            if (abs(center.x) > center.w ||
                abs(center.y) > center.w ||
                abs(center.z) > center.w) {
                gl_Position = vec4(2.0, 2.0, 2.0, 1.0);
                return;
            }

            // final vertex position
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
            vec3 light_dir = normalize(vec3(0.0, 0.0, 1.0)); // light direction
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
            pygame.display.set_caption("3D Rendering - OpenGL")

            print(f"[OpenGL] {glGetString(GL_VERSION).decode()}")
            glViewport(0, 0, *display)

            prog = link_prog(VERT_GLSL, FRAG_GLSL)
            glUseProgram(prog)
            mvp_loc = glGetUniformLocation(prog, "mvp")

            faces, normals, face_flags, edges, edge_flags = self.make_cube_geometry()

            def interleave(verts, flags):
                return np.column_stack([verts, flags]).astype(np.float32)

            face_data = interleave(faces, face_flags)
            edge_data = interleave(edges, edge_flags)

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

            chunk_data, chunk_bounds = self.get_chunks()

            chunk_vbos = {}

            for key, pts in chunk_data.items():
                vbo = glGenBuffers(1)
                glBindBuffer(GL_ARRAY_BUFFER, vbo)
                glBufferData(GL_ARRAY_BUFFER, pts.nbytes, pts, GL_STATIC_DRAW)
                chunk_vbos[key] = (vbo, len(pts))

            print(f"[Chunks] Total: {len(chunk_data)} | Example: {list(chunk_data.keys())[:5]}")

            glEnable(GL_DEPTH_TEST)
            glEnable(GL_CULL_FACE)
            glCullFace(GL_BACK)

            clock = pygame.time.Clock()
            running = True

            cam = {"x": self.CX, "y": self.CY + 10, "z": self.CZ + 80, "yaw": -90, "pitch": -20, "speed": 1.2}

            visible_generations = 100


            while running:
                for e in pygame.event.get():
                    if e.type == pygame.QUIT:
                        running = False
                    

                keys = pygame.key.get_pressed()

                if keys[pygame.K_w]:
                    cam["x"] += cam["speed"] * np.cos(np.radians(cam["yaw"]))
                    cam["z"] += cam["speed"] * np.sin(np.radians(cam["yaw"]))

                if keys[pygame.K_s]:
                    cam["x"] -= cam["speed"] * np.cos(np.radians(cam["yaw"]))
                    cam["z"] -= cam["speed"] * np.sin(np.radians(cam["yaw"]))

                if keys[pygame.K_a]:
                    cam["x"] += cam["speed"] * np.cos(np.radians(cam["yaw"] - 90))
                    cam["z"] += cam["speed"] * np.sin(np.radians(cam["yaw"] - 90))

                if keys[pygame.K_d]:
                    cam["x"] += cam["speed"] * np.cos(np.radians(cam["yaw"] + 90))
                    cam["z"] += cam["speed"] * np.sin(np.radians(cam["yaw"] + 90))

                if keys[pygame.K_SPACE]:
                    cam["y"] += cam["speed"]

                if keys[pygame.K_LSHIFT]:
                    cam["y"] -= cam["speed"]

                if keys[pygame.K_LEFT]:
                    cam["yaw"] -= 3

                if keys[pygame.K_RIGHT]:
                    cam["yaw"] += 3

                if keys[pygame.K_UP]:
                    cam["pitch"] = min(89, cam["pitch"] + 3)

                if keys[pygame.K_DOWN]:
                    cam["pitch"] = max(-89, cam["pitch"] - 3)

                if keys[pygame.K_r]:
                    cam["x"] = self.CX
                    cam["y"] = self.CY + 10
                    cam["z"] = self.CZ + 80
                    cam["yaw"] = -90
                    cam["pitch"] = -20

                if keys[pygame.K_i] or keys[pygame.K_KP_PLUS]:
                    visible_generations = min(1000, visible_generations + 1)

                if keys[pygame.K_o] or keys[pygame.K_KP_MINUS]:
                    visible_generations = max(1, visible_generations - 1)

                mvp = self.compute_mvp(cam["x"], cam["y"], cam["z"], cam["yaw"], cam["pitch"])

                glClearColor(0.1, 0.1, 0.2, 1.0)
                glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

                glUseProgram(prog)
                #print("MVP:\n", mvp)

                planes = self.extract_frustum_planes(mvp)
                #print(f"Frustum planes: {len(planes)}")

                visible_chunks = []

                for key, (min_p, max_p) in chunk_bounds.items():
                    if self.aabb_in_frustum_minmax(planes, min_p, max_p):
                        visible_chunks.append(key)
                    
                # Visible chunks:
                #print(f"Visible chunks: {len(visible_chunks)} / {len(chunk_bounds)}")

                glUniformMatrix4fv(mvp_loc, 1, GL_FALSE, mvp.T)

                visible_pts = []

                for key in visible_chunks:
                    pts = chunk_data[key]
                    pts = pts[pts[:, 2] >= visible_generations]

                    if len(pts):
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