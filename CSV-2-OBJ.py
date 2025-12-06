import csv
import os
import sys

# ==================== USER SETTINGS =======================
# KEEPING your original config

POSITION_INDEX = (2, 3, 4)   # (X, Y, Z)
UV_INDEX = (5, 6)            # (U, V)
MIRROR_Z = True              # Flip Z for correct orientation
SHADE_SMOOTH = True          # NEW: Auto "shade smooth" flag
REMOVE_DOUBLES = True        # NEW: Remove duplicate vertices

# ==========================================================


def read_float(row, idx, default=0.0):
    """Safe CSV → float conversion."""
    try:
        return float(row[idx])
    except Exception:
        return default


def parse_csv(csv_path):
    verts = []
    uvs = []
    raw_faces = []

    with open(csv_path, newline='') as f:
        reader = csv.reader(f)
        next(reader)

        face_build = []

        for i, row in enumerate(reader):
            x = read_float(row, POSITION_INDEX[0])
            y = read_float(row, POSITION_INDEX[1])
            z = read_float(row, POSITION_INDEX[2])

            if MIRROR_Z:
                z = -z

            verts.append((x, y, z))

            u = read_float(row, UV_INDEX[0])
            v = read_float(row, UV_INDEX[1])

            # Puxtril's UV correction
            v = 1.0 - v
            uvs.append((u, v))

            # Build faces every 3 vertices
            face_build.append(i)
            if len(face_build) == 3:
                raw_faces.append(tuple(face_build))
                face_build = []

    return verts, uvs, raw_faces


def remove_duplicate_vertices(verts, uvs, faces):
    """Puxtril-style deduplication (fast vertex hashing)."""

    if not REMOVE_DOUBLES:
        return verts, uvs, faces

    vert_map = {}
    new_verts = []
    new_uvs = []
    index_map = {}
    next_index = 0

    # Reindex vertices
    for old_index, (v, uv) in enumerate(zip(verts, uvs)):
        key = (round(v[0], 6), round(v[1], 6), round(v[2], 6),
               round(uv[0], 6), round(uv[1], 6))

        if key not in vert_map:
            vert_map[key] = next_index
            new_verts.append(v)
            new_uvs.append(uv)
            next_index += 1

        index_map[old_index] = vert_map[key]

    # Rebuild faces using new indices
    new_faces = []
    for f in faces:
        a = index_map[f[0]]
        b = index_map[f[1]]
        c = index_map[f[2]]
        if a != b != c:  # avoid collapsed faces
            new_faces.append((a, b, c))

    return new_verts, new_uvs, new_faces


def write_obj(obj_path, verts, uvs, faces):
    with open(obj_path, 'w') as f:
        f.write("# Exported from CSV\n")

        for v in verts:
            f.write(f"v {v[0]} {v[1]} {v[2]}\n")

        for uv in uvs:
            f.write(f"vt {uv[0]} {uv[1]}\n")

        # Optional smooth shading
        if SHADE_SMOOTH:
            f.write("s 1\n")
        else:
            f.write("s off\n")

        for (a, b, c) in faces:
            ia = a + 1
            ib = b + 1
            ic = c + 1
            f.write(f"f {ia}/{ia} {ib}/{ib} {ic}/{ic}\n")


def convert_csv_to_obj(csv_path):
    verts, uvs, faces = parse_csv(csv_path)

    verts, uvs, faces = remove_duplicate_vertices(verts, uvs, faces)

    obj_path = os.path.splitext(csv_path)[0] + ".obj"
    write_obj(obj_path, verts, uvs, faces)

    print(f"Saved: {obj_path}")


def main():
    if len(sys.argv) < 2:
        print("Drag & Drop CSV files onto this script.")
        return

    for arg in sys.argv[1:]:
        if arg.lower().endswith(".csv") and os.path.isfile(arg):
            try:
                print(f"Processing: {arg}")
                convert_csv_to_obj(arg)
            except Exception as e:
                print(f"Error: {e}")
        else:
            print(f"Skipped: {arg}")

if __name__ == "__main__":
    main()
