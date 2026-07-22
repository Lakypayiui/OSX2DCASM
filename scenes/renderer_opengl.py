"""OpenGL (Pygame) renderer for 3D Game-of-Life visualization.

Provides a standalone function ``run_opengl_renderer`` that opens a Pygame
window backed by OpenGL 4.1 Core and renders cube instances for each living
cell using instanced drawing and chunk-based frustum culling.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
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
    GL_CULL_FACE, GL_BACK, glCullFace, glBufferSubData,
)

if TYPE_CHECKING:
    from scenes.display3dscene import Display3DScene


VERT_GLSL = """\
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

FRAG_GLSL = """\
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


def _compile_shader(src: str, kind: int) -> int:
    """Compile a single GLSL shader stage and return its handle.

    Args:
        src: GLSL source code string.
        kind: Shader kind (e.g. ``GL_VERTEX_SHADER``).

    Returns:
        OpenGL shader object handle.

    Raises:
        RuntimeError: If compilation fails.
    """
    sh = glCreateShader(kind)
    glShaderSource(sh, src)
    glCompileShader(sh)
    if not glGetShaderiv(sh, GL_COMPILE_STATUS):
        raise RuntimeError(glGetShaderInfoLog(sh).decode())
    return sh


def _link_prog(vs_src: str, fs_src: str) -> int:
    """Compile and link a vertex+fragment shader pair into a program.

    Args:
        vs_src: Vertex shader GLSL source.
        fs_src: Fragment shader GLSL source.

    Returns:
        OpenGL program object handle.

    Raises:
        RuntimeError: If linking fails.
    """
    vs = _compile_shader(vs_src, GL_VERTEX_SHADER)
    fs = _compile_shader(fs_src, GL_FRAGMENT_SHADER)
    p = glCreateProgram()
    glAttachShader(p, vs)
    glAttachShader(p, fs)
    glLinkProgram(p)
    glDeleteShader(vs)
    glDeleteShader(fs)
    if not glGetProgramiv(p, GL_LINK_STATUS):
        raise RuntimeError(glGetProgramInfoLog(p).decode())
    return p


def _interleave(verts: np.ndarray, flags: np.ndarray) -> np.ndarray:
    """Column-stack vertex data with per-vertex flags."""
    return np.column_stack([verts, flags]).astype(np.float32)


def _build_vao(
    verts: np.ndarray,
    flags: np.ndarray,
    normals: np.ndarray,
) -> tuple[int, int]:
    """Create a VAO with position (loc=0), edge flag (loc=1), and normal (loc=3).

    Args:
        verts: ``(N, 3)`` vertex positions.
        flags: ``(N,)`` or ``(N, 1)`` edge flags.
        normals: ``(N, 3)`` normal vectors.

    Returns:
        ``(vao_handle, vertex_count)`` tuple.
    """
    vao = glGenVertexArrays(1)
    glBindVertexArray(vao)

    for loc, data, n_comp in [
        (0, verts, 3),
        (1, flags[:, None] if flags.ndim == 1 else flags, 1),
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


def run_opengl_renderer(dsp: "Display3DScene") -> None:
    """Launch the OpenGL-based 3D renderer for the given Display3DScene instance.

    Opens a Pygame window backed by OpenGL 4.1 Core and enters the render
    loop.  All shared geometry / math methods are called on *dsp*.

    Args:
        dsp: Fully-initialised ``Display3DScene`` instance containing grid data,
            camera anchor points, and shared helper methods.

    Note:
        This function blocks until the user closes the window.
    """
    pygame.init()
    display = (dsp.width, dsp.height)
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 4)
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 1)
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_PROFILE_MASK,
                                    pygame.GL_CONTEXT_PROFILE_CORE)
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_FORWARD_COMPATIBLE_FLAG, True)
    pygame.display.set_mode(display, DOUBLEBUF | OPENGL)
    pygame.display.set_caption("3D Rendering - OpenGL")

    print(f"[OpenGL] {glGetString(GL_VERSION).decode()}")
    glViewport(0, 0, *display)

    prog = _link_prog(VERT_GLSL, FRAG_GLSL)
    glUseProgram(prog)
    mvp_loc = glGetUniformLocation(prog, "mvp")

    faces, normals, face_flags, edges, edge_flags = dsp.make_cube_geometry()

    face_data = _interleave(faces, face_flags)
    edge_data = _interleave(edges, edge_flags)

    vao_f, n_fv = _build_vao(faces, face_flags, normals)
    vao_e, n_ev = _build_vao(edges, edge_flags, normals)

    chunk_data, chunk_bounds = dsp.get_chunks()

    chunk_vbos: dict[tuple, tuple[int, int]] = {}

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

    cam = {"x": dsp.CX, "y": dsp.CY + 10, "z": dsp.CZ + 80, "yaw": -90, "pitch": -20, "speed": 1.2}

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
            cam["x"] = dsp.CX
            cam["y"] = dsp.CY + 10
            cam["z"] = dsp.CZ + 80
            cam["yaw"] = -90
            cam["pitch"] = -20

        if keys[pygame.K_i] or keys[pygame.K_KP_PLUS]:
            visible_generations = min(1000, visible_generations + 1)

        if keys[pygame.K_o] or keys[pygame.K_KP_MINUS]:
            visible_generations = max(1, visible_generations - 1)

        mvp = dsp.compute_mvp(cam["x"], cam["y"], cam["z"], cam["yaw"], cam["pitch"])

        glClearColor(0.1, 0.1, 0.2, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        glUseProgram(prog)
        # print("MVP:\n", mvp)

        planes = dsp.extract_frustum_planes(mvp)
        # print(f"Frustum planes: {len(planes)}")

        visible_chunks = []

        for key, (min_p, max_p) in chunk_bounds.items():
            if dsp.aabb_in_frustum_minmax(planes, min_p, max_p):
                visible_chunks.append(key)

        # Visible chunks:
        # print(f"Visible chunks: {len(visible_chunks)} / {len(chunk_bounds)}")

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

        max_points = len(dsp.all_points)

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

        # print("-" * 60)

        pygame.display.flip()
        clock.tick(60)
