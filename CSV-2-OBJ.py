import csv
import os
import sys

# ==================== USER SETTINGS =======================
# CHANGE THESE if your CSV has different column structure

POSITION_INDEX = (2, 3, 4)  # X, Y, Z column indices
UV_INDEX = (5, 6)           # U, V column indices
MIRROR_Z = True             # Mirrors geometry's Z (For original orientation)

# Remember to Select All by pressing 'A' and Merge (By Distance) by 'M' in Edit Mode
# Don't forget to Shde Smooth the model (Right mouse button in Object mode)
# ==========================================================

def read_float(row, idx, default=0.0):
    """Read a float from the CSV row, with error handling."""
    try:
        return float(row[idx])
    except Exception:
        return default

def parse_csv(csv_path):
    verts = []
    uvs = []
    faces = []

    with open(csv_path, newline='') as f:
        reader = csv.reader(f)
        
        # Automatically skip the header row
        next(reader)

        face_indices = []
        vert_index = 1  # OBJ indices start from 1

        for row in reader:
            # Read vertex positions
            x = read_float(row, POSITION_INDEX[0])
            y = read_float(row, POSITION_INDEX[1])
            z = read_float(row, POSITION_INDEX[2])

            if MIRROR_Z:
                z = -z  # Apply Z-axis mirroring

            verts.append((x, y, z))

            # Read UVs
            u = read_float(row, UV_INDEX[0])
            v = read_float(row, UV_INDEX[1])
            uvs.append((u, v))

            # Add to face buffer
            face_indices.append(vert_index)
            if len(face_indices) == 3:
                faces.append(tuple(face_indices))
                face_indices = []

            vert_index += 1

    return verts, uvs, faces

def write_obj(obj_path, verts, uvs, faces):
    with open(obj_path, 'w') as f:
        f.write("# Exported from CSV with topology preserved\n")

        # Write vertices
        for v in verts:
            f.write(f"v {v[0]} {v[1]} {v[2]}\n")
        
        # Write UVs
        for uv in uvs:
            f.write(f"vt {uv[0]} {uv[1]}\n")
        
        # Write faces
        for face in faces:
            f.write("f " + " ".join(f"{i}/{i}" for i in face) + "\n")

def convert_csv_to_obj(csv_path):
    verts, uvs, faces = parse_csv(csv_path)
    obj_path = os.path.splitext(csv_path)[0] + ".obj"
    write_obj(obj_path, verts, uvs, faces)
    print(f"✅ Saved: {obj_path}")

def main():
    if len(sys.argv) < 2:
        print("📌 Drag and drop one or more CSV files onto this script.")
        return

    for arg in sys.argv[1:]:
        if arg.lower().endswith(".csv") and os.path.isfile(arg):
            try:
                print(f"📄 Processing: {arg}")
                convert_csv_to_obj(arg)
            except Exception as e:
                print(f"❌ Error processing {arg}: {e}")
        else:
            print(f"⚠️ Skipped: {arg} (not a .csv file)")

if __name__ == "__main__":
    main()

