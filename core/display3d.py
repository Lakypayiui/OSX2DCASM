

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

    def macos_3d_render(self) -> None:
        """Launch the Metal-based 3D renderer (macOS only).

        Delegates to :func:`core.renderer_metal.run_metal_renderer`.
        """
        from core.renderer_metal import run_metal_renderer
        run_metal_renderer(self)

    def open_gl_render(self) -> None:
        """Launch the OpenGL-based 3D renderer.

        Delegates to :func:`core.renderer_opengl.run_opengl_renderer`.
        """
        from core.renderer_opengl import run_opengl_renderer
        run_opengl_renderer(self)

