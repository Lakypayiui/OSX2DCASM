"""Metal GPU renderer for 3D Game-of-Life visualization (macOS only).

Provides a standalone function ``run_metal_renderer`` that opens a GLFW window
backed by Apple's Metal API and renders cube instances for each living cell.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from scenes.display3dscene import Display3DScene


def run_metal_renderer(dsp: "Display3DScene") -> None:
    """Launch the Metal-based 3D renderer for the given Display3D instance.

    Opens a native GLFW+Metal window and enters the render loop.  All shared
    geometry / math methods (``make_cube_geometry``, ``compute_mvp``, etc.) are
    called on *dsp* so the ``Display3D`` class stays the single owner of those
    routines.

    Args:
        dsp: Fully-initialised ``Display3D`` instance containing grid data,
            camera anchor points, and shared helper methods.

    Note:
        This function blocks until the user closes the window.  It imports
        macOS-specific frameworks (Metal, GLFW, PyObjC) and is only intended
        to be called on ``Darwin``.
    """
    # macOS-specific imports (only available on Darwin)
    import ctypes
    from ctypes import cdll, c_void_p
    import glfw
    import Metal
    import objc
    from Foundation import NSAutoreleasePool

    print(f"[Metal 3D] Starting render from PID = {os.getpid()}")

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
    window = glfw.create_window(dsp.width, dsp.height, "Game of Life 3D [Metal]", None, None)
    if not window:
        glfw.terminate()
        raise RuntimeError("No window")

    pool = NSAutoreleasePool.alloc().init()
    devices = Metal.MTLCopyAllDevices()
    device = next((d for d in devices if "radeon" in d.name().lower() or "amd" in d.name().lower()), devices[0])
    print(device)

    # Layer setup
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
    except Exception:
        pass

    # Pipeline and buffers
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
    dsp.pipeline = pipeline
    dsp.depth_state = depth_state

    # Geometry
    faces, _, face_flags, edges, edge_flags = dsp.make_cube_geometry()

    def interleave(verts, flags):
        return np.column_stack([verts, flags]).astype(np.float32)

    face_data = interleave(faces, face_flags)
    edge_data = interleave(edges, edge_flags)

    def make_buf(data):
        arr = np.ascontiguousarray(data, dtype=np.float32)
        return device.newBufferWithBytes_length_options_(arr.tobytes(), arr.nbytes, Metal.MTLResourceStorageModeShared)

    vbuf_faces = make_buf(face_data)
    vbuf_edges = make_buf(edge_data)
    offsets_buf = make_buf(dsp.all_points)

    uniform_buffers = [device.newBufferWithLength_options_(64, Metal.MTLResourceStorageModeShared) for _ in range(3)]
    current_uniform_idx = 0
    n_fv = len(face_data)
    n_ev = len(edge_data)

    # Safer initial camera
    cam = {"x": dsp.CX, "y": dsp.CY + 10, "z": dsp.CZ + 80, "yaw": -90, "pitch": -20, "speed": 1.2}
    S = {"w": dsp.width, "h": dsp.height, "dirty": True}
    dsp.last_generation = getattr(dsp, 'generation', 0)
    dsp.depth_tex = None

    cmd_queue = device.newCommandQueue()
    print(f"[DEBUG] Centered at ({dsp.CX:.1f}, {dsp.CY:.1f}, {dsp.CZ:.1f}) | Cells: {dsp.N}")

    def update_metal_buffer(metal_buf, np_array):
        data_bytes = np_array.tobytes()
        # PyObjC wraps the void* in an objc.varlist.
        # .as_buffer(size) gives direct access to that C memory to overwrite it.
        metal_buf.contents().as_buffer(len(data_bytes))[:] = data_bytes

    # Make sure to define this BEFORE the while if you haven't
    # visible_generations = 50

    while not glfw.window_should_close(window):
        glfw.poll_events()

        def key(k):
            return glfw.get_key(window, k) == glfw.PRESS

        moved = False

        if key(glfw.KEY_W):
            cam["x"] += cam["speed"] * np.cos(np.radians(cam["yaw"]))
            cam["z"] += cam["speed"] * np.sin(np.radians(cam["yaw"]))
            moved = True
        if key(glfw.KEY_S):
            cam["x"] -= cam["speed"] * np.cos(np.radians(cam["yaw"]))
            cam["z"] -= cam["speed"] * np.sin(np.radians(cam["yaw"]))
            moved = True
        if key(glfw.KEY_A):
            cam["x"] += cam["speed"] * np.cos(np.radians(cam["yaw"] - 90))
            cam["z"] += cam["speed"] * np.sin(np.radians(cam["yaw"] - 90))
            moved = True
        if key(glfw.KEY_D):
            cam["x"] += cam["speed"] * np.cos(np.radians(cam["yaw"] + 90))
            cam["z"] += cam["speed"] * np.sin(np.radians(cam["yaw"] + 90))
            moved = True
        if key(glfw.KEY_SPACE):
            cam["y"] += cam["speed"]
            moved = True
        if key(glfw.KEY_LEFT_SHIFT):
            cam["y"] -= cam["speed"]
            moved = True

        if key(glfw.KEY_LEFT):
            cam["yaw"] -= 3
            moved = True
        if key(glfw.KEY_RIGHT):
            cam["yaw"] += 3
            moved = True
        if key(glfw.KEY_UP):
            cam["pitch"] = min(89, cam["pitch"] + 3)
            moved = True
        if key(glfw.KEY_DOWN):
            cam["pitch"] = max(-89, cam["pitch"] - 3)
            moved = True

        if key(glfw.KEY_R):
            cam["x"] = dsp.CX
            cam["y"] = dsp.CY + 10
            cam["z"] = dsp.CZ + 80
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
        mvp = dsp.compute_mvp(cam["x"], cam["y"], cam["z"], cam["yaw"], cam["pitch"])

        # --- DISTANCE FILTERING (CULLING) ---
        dist_z = np.abs(dsp.all_points[:, 2] - cam["z"])
        mask = dist_z <= visible_generations
        visible_points = dsp.all_points[mask]

        # Get the new instance count to draw
        instance_count = len(visible_points)

        # Update the buffer ONLY with visible points
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
        if dsp.depth_tex is None or (fw, fh) != (S["w"], S["h"]):
            td = Metal.MTLTextureDescriptor.texture2DDescriptorWithPixelFormat_width_height_mipmapped_(depth_fmt, fw, fh, False)
            td.setUsage_(Metal.MTLTextureUsageRenderTarget)
            td.setStorageMode_(Metal.MTLStorageModePrivate)
            dsp.depth_tex = device.newTextureWithDescriptor_(td)
            layer.setDrawableSize_((fw, fh))
            S["w"], S["h"] = fw, fh

        rpd = Metal.MTLRenderPassDescriptor.renderPassDescriptor()
        color_att = rpd.colorAttachments().objectAtIndexedSubscript_(0)
        color_att.setTexture_(drawable.texture())
        color_att.setLoadAction_(Metal.MTLLoadActionClear)
        # Dark blue to confirm Metal is clearing the frame
        color_att.setClearColor_(Metal.MTLClearColorMake(0.1, 0.1, 0.2, 1.0))
        color_att.setStoreAction_(Metal.MTLStoreActionStore)

        rpd.depthAttachment().setTexture_(dsp.depth_tex)
        rpd.depthAttachment().setLoadAction_(Metal.MTLLoadActionClear)
        rpd.depthAttachment().setClearDepth_(1.0)
        rpd.depthAttachment().setStoreAction_(Metal.MTLStoreActionDontCare)

        cmd_buf = cmd_queue.commandBuffer()
        enc = cmd_buf.renderCommandEncoderWithDescriptor_(rpd)
        enc.setRenderPipelineState_(dsp.pipeline)
        enc.setDepthStencilState_(dsp.depth_state)

        # Draw call
        enc.setVertexBuffer_offset_atIndex_(uniform_buf, 0, 2)

        if instance_count > 0:
            # Faces
            enc.setVertexBuffer_offset_atIndex_(vbuf_faces, 0, 0)
            enc.setVertexBuffer_offset_atIndex_(offsets_buf, 0, 1)
            enc.drawPrimitives_vertexStart_vertexCount_instanceCount_(Metal.MTLPrimitiveTypeTriangle, 0, n_fv, instance_count)

            # Edges
            enc.setVertexBuffer_offset_atIndex_(vbuf_edges, 0, 0)
            enc.setVertexBuffer_offset_atIndex_(offsets_buf, 0, 1)
            enc.drawPrimitives_vertexStart_vertexCount_instanceCount_(Metal.MTLPrimitiveTypeLine, 0, n_ev, instance_count)

        enc.endEncoding()
        cmd_buf.presentDrawable_(drawable)
        cmd_buf.commit()

    glfw.destroy_window(window)
    glfw.terminate()
    del pool
