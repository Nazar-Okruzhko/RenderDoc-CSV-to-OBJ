import struct
import sys
import os
import traceback
import json
import array

DEBUG_MODE = False
FLIP_UV_VERTICALLY = True
EXPORT_GLB = False

UV_OFFSET_MAP = {
    184: 60,
    160: 52,
    56: 48,
    20: 12,
}

def safe_read(f, size, desc=""):
    data = f.read(size)
    if len(data) != size:
        raise EOFError(f"Unexpected end of file while reading {desc} ({len(data)}/{size} bytes)")
    return data

def read_int32(f):
    return struct.unpack("<I", safe_read(f, 4, "int32"))[0]

def read_float(f):
    return struct.unpack("<f", safe_read(f, 4, "float"))[0]

def find_dds_textures(f):
    f.seek(0, 0)
    data = f.read()
    pattern = b'.dds\x00'
    
    textures = []
    search_pos = 0
    
    while len(textures) < 3:
        pos = data.find(pattern, search_pos)
        if pos == -1:
            break
        
        start = pos
        while start > 0 and data[start - 1] not in [0x00, 0xFF]:
            start -= 1
        
        texture_name = data[start:pos + 4].decode('ascii', errors='ignore')
        if texture_name and texture_name not in textures:
            textures.append(texture_name)
            print(f"Found texture #{len(textures)}: {texture_name}")
        
        search_pos = pos + len(pattern)
    
    return textures

def find_face_start(f):
    f.seek(0, 0)
    data = f.read()
    pattern = b'\x00\x00\x00\x00\x01\x00\x00\x00\x02\x00\x00\x00'
    
    pos = data.find(pattern)
    if pos == -1:
        raise ValueError("Face start pattern (0, 1, 2) not found in file")
    
    print(f"Found face start pattern at 0x{pos:08X}")
    f.seek(pos, 0)
    return f.tell()

def write_mtl_file(mtl_path, obj_basename, textures):
    try:
        with open(mtl_path, "w", encoding="utf-8") as mtl:
            mtl.write("# Blender 3.6.23 LTS\n")
            mtl.write("# www.blender.org\n\n")
            mtl.write(f"newmtl {obj_basename}\n")
            mtl.write("Ns 0.000000\n")
            mtl.write("Ka 1.000000 1.000000 1.000000\n")
            mtl.write("Ke 0.000000 0.000000 0.000000\n")
            mtl.write("Ni 1.450000\n")
            mtl.write("d 1.000000\n")
            mtl.write("illum 2\n")
            
            if len(textures) >= 1:
                mtl.write(f"map_Kd {textures[0]}\n")
            
            if len(textures) >= 3:
                mtl.write(f"map_Ks {textures[2]}\n")
            
            if len(textures) >= 2:
                mtl.write(f"\nmap_Bump -bm 1.000000 {textures[1]}\n")
        
        print(f"✓ Wrote MTL: {mtl_path}")
    except Exception as e:
        print(f"✖ ERROR writing MTL file: {e}")

def load_dds_files(rip_path, textures):
    dds_data = []
    directory = os.path.dirname(rip_path)
    
    for tex_name in textures:
        tex_path = os.path.join(directory, tex_name)
        try:
            if os.path.exists(tex_path):
                with open(tex_path, "rb") as f:
                    dds_bytes = f.read()
                    dds_data.append({'name': tex_name, 'data': dds_bytes})
                    print(f"Loaded {tex_name}: {len(dds_bytes)} bytes")
            else:
                print(f"⚠ Texture not found: {tex_path}")
        except Exception as e:
            print(f"⚠ Error loading {tex_name}: {e}")
    
    return dds_data

def create_glb(vertices, normals, uvs, faces, textures, dds_data, output_path, model_name):
    try:
        print(f"\nCreating GLB file...")
        
        vertex_data = array.array('f')
        for v in vertices:
            vertex_data.extend(v)
        vertex_bytes = vertex_data.tobytes()
        
        normal_data = array.array('f')
        for n in normals:
            normal_data.extend(n)
        normal_bytes = normal_data.tobytes()
        
        uv_bytes = b''
        if uvs:
            uv_data = array.array('f')
            for uv in uvs:
                # Flip V coordinate again for GLB to match OBJ appearance in Blender
                u, v = uv
                v_flipped = 1.0 - v
                uv_data.extend([u, v_flipped])
            uv_bytes = uv_data.tobytes()
        
        indices_data = array.array('I')
        for face in faces:
            indices_data.extend([face[0]-1, face[1]-1, face[2]-1])
        indices_bytes = indices_data.tobytes()
        
        buffer_data = vertex_bytes + normal_bytes + uv_bytes + indices_bytes
        
        texture_buffers = []
        for dds in dds_data:
            texture_buffers.append(dds['data'])
            buffer_data += dds['data']
        
        buffer_length = len(buffer_data)
        
        accessors = [
            {"bufferView": 0, "componentType": 5126, "count": len(vertices), "type": "VEC3", "max": [max(v[0] for v in vertices), max(v[1] for v in vertices), max(v[2] for v in vertices)], "min": [min(v[0] for v in vertices), min(v[1] for v in vertices), min(v[2] for v in vertices)]},
            {"bufferView": 1, "componentType": 5126, "count": len(normals), "type": "VEC3"},
        ]
        
        buffer_views = [
            {"buffer": 0, "byteOffset": 0, "byteLength": len(vertex_bytes), "target": 34962},
            {"buffer": 0, "byteOffset": len(vertex_bytes), "byteLength": len(normal_bytes), "target": 34962},
        ]
        
        attributes = {"POSITION": 0, "NORMAL": 1}
        
        if uvs:
            accessors.append({"bufferView": 2, "componentType": 5126, "count": len(uvs), "type": "VEC2"})
            buffer_views.append({"buffer": 0, "byteOffset": len(vertex_bytes) + len(normal_bytes), "byteLength": len(uv_bytes), "target": 34962})
            attributes["TEXCOORD_0"] = 2
        
        indices_offset = len(vertex_bytes) + len(normal_bytes) + len(uv_bytes)
        accessors.append({"bufferView": len(buffer_views), "componentType": 5125, "count": len(faces) * 3, "type": "SCALAR"})
        buffer_views.append({"buffer": 0, "byteOffset": indices_offset, "byteLength": len(indices_bytes), "target": 34963})
        
        current_offset = indices_offset + len(indices_bytes)
        images = []
        for i, dds in enumerate(dds_data):
            buffer_views.append({"buffer": 0, "byteOffset": current_offset, "byteLength": len(dds['data'])})
            images.append({"bufferView": len(buffer_views) - 1, "mimeType": "image/vnd-ms.dds", "name": dds['name']})
            current_offset += len(dds['data'])
        
        gltf = {
            "asset": {"version": "2.0", "generator": "NinjaRipper-OBJ Converter"},
            "scene": 0,
            "scenes": [{"nodes": [0]}],
            "nodes": [{"mesh": 0}],
            "meshes": [{"name": model_name, "primitives": [{"attributes": attributes, "indices": len(accessors) - 1}]}],
            "accessors": accessors,
            "bufferViews": buffer_views,
            "buffers": [{"byteLength": buffer_length}]
        }
        
        if dds_data:
            gltf["images"] = images
            gltf["textures"] = [{"source": i} for i in range(len(dds_data))]
            
            material = {"name": model_name, "pbrMetallicRoughness": {"metallicFactor": 0.0}}
            
            if len(dds_data) >= 1:
                material["pbrMetallicRoughness"]["baseColorTexture"] = {"index": 0}
            if len(dds_data) >= 2:
                material["normalTexture"] = {"index": 1}
            if len(dds_data) >= 3:
                material["pbrMetallicRoughness"]["metallicRoughnessTexture"] = {"index": 2}
            
            gltf["materials"] = [material]
            gltf["meshes"][0]["primitives"][0]["material"] = 0
        
        gltf_json = json.dumps(gltf, separators=(',', ':')).encode('utf-8')
        gltf_json_length = len(gltf_json)
        gltf_json_padding = (4 - (gltf_json_length % 4)) % 4
        gltf_json += b' ' * gltf_json_padding
        
        buffer_padding = (4 - (buffer_length % 4)) % 4
        buffer_data += b'\x00' * buffer_padding
        
        total_length = 12 + 8 + len(gltf_json) + 8 + len(buffer_data)
        
        with open(output_path, 'wb') as f:
            f.write(struct.pack('<I', 0x46546C67))
            f.write(struct.pack('<I', 2))
            f.write(struct.pack('<I', total_length))
            
            f.write(struct.pack('<I', len(gltf_json)))
            f.write(struct.pack('<I', 0x4E4F534A))
            f.write(gltf_json)
            
            f.write(struct.pack('<I', len(buffer_data)))
            f.write(struct.pack('<I', 0x004E4942))
            f.write(buffer_data)
        
        print(f"✓ Created GLB: {output_path}")
        print(f"  Vertices: {len(vertices)}, Faces: {len(faces)}, Textures: {len(dds_data)}\n")
        
    except Exception as e:
        print(f"✖ ERROR creating GLB: {e}")
        traceback.print_exc()

def convert_rip_to_obj(input_path):
    print(f"Processing: {input_path}\n")
    
    base_name = os.path.splitext(os.path.basename(input_path))[0]
    output_dir = os.path.dirname(input_path) if os.path.dirname(input_path) else "."
    
    if EXPORT_GLB:
        output_path = os.path.join(output_dir, base_name + ".glb")
        print("GLB export mode enabled\n")
    else:
        output_path = os.path.join(output_dir, base_name + ".obj")
        mtl_path = os.path.join(output_dir, base_name + ".mtl")

    vertices, normals, uvs, faces = [], [], [], []
    textures = []
    dds_data = []

    try:
        print("Searching for DDS textures...")
        with open(input_path, "rb") as f:
            textures = find_dds_textures(f)
        
        if textures:
            print(f"Found {len(textures)} texture(s)\n")
        else:
            print("⚠ No textures found\n")

        with open(input_path, "rb") as f:
            f.seek(0, 0)
            header_magic = safe_read(f, 8, "Header Magic")
            print(f"Header Magic: {header_magic.hex().upper()}")

            f.seek(0x8)
            face_count = read_int32(f)
            f.seek(0xC)
            vert_count = read_int32(f)
            f.seek(0x10)
            stride = read_int32(f)

            print(f"Faces = {face_count}, Vertex count = {vert_count}, Stride = {stride}")

            uv_offset = UV_OFFSET_MAP.get(stride)
            if uv_offset is not None:
                uv_stride = stride + 4
                print(f"UV Coord Stride = {uv_stride} (Vertex Stride {stride} + 4 bytes)")
            else:
                print(f"⚠ Warning: No UV offset mapping for stride {stride}. UVs will not be extracted.")
                uv_offset = None

            face_start = find_face_start(f)
            print(f"Starting face extraction at 0x{face_start:08X}")

            f.seek(face_start, 0)
            for _ in range(face_count):
                i1 = read_int32(f)
                i2 = read_int32(f)
                i3 = read_int32(f)
                faces.append((i1 + 1, i2 + 1, i3 + 1))

            vertex_data_start = f.tell()
            for i in range(vert_count):
                vertex_block_start = vertex_data_start + i * stride
                f.seek(vertex_block_start)

                if DEBUG_MODE:
                    print(f"[VERTEX BLOCK ADDRESS] Vertex {i}: 0x{vertex_block_start:08X}")

                vx = read_float(f)
                vy = read_float(f)
                vz = read_float(f)
                vertices.append((vx, vy, vz))

                normal_block_start = f.tell()
                nx = read_float(f)
                ny = read_float(f)
                nz = read_float(f)
                normals.append((nx, ny, nz))

                if DEBUG_MODE:
                    print(f"[NORMAL BLOCK ADDRESS] Vertex {i}: 0x{normal_block_start:08X}")

                if uv_offset is not None:
                    uv_block_start = vertex_block_start + uv_offset
                    f.seek(uv_block_start)
                    
                    if DEBUG_MODE:
                        print(f"[UV COORD BLOCK ADDRESS] Vertex {i}: 0x{uv_block_start:08X}")
                    
                    u = read_float(f)
                    v = read_float(f)
                    
                    # Apply UV flip for both OBJ and GLB when enabled
                    if FLIP_UV_VERTICALLY:
                        v = 1.0 - v
                    
                    uvs.append((u, v))

            print(f"\nExtracted {len(vertices)} vertices, {len(normals)} normals", end="")
            if uvs:
                print(f", and {len(uvs)} UV coordinates.")
            else:
                print(".")
            
            if EXPORT_GLB and textures:
                print("\nLoading DDS texture files...")
                dds_data = load_dds_files(input_path, textures)

    except Exception as e:
        print("\n✖ WARNING – Converter crashed while reading:")
        print(type(e).__name__, ":", e)
        traceback.print_exc()
        print("\nAttempting to write out whatever was read so far...")

    if EXPORT_GLB:
        create_glb(vertices, normals, uvs, faces, textures, dds_data, output_path, base_name)
    else:
        if textures:
            write_mtl_file(mtl_path, base_name, textures)
        else:
            print("No textures found, skipping MTL file creation.")

        try:
            with open(output_path, "w", encoding="utf-8") as out:
                out.write("# NinjaRipper Reborn\n\n")
                
                if textures:
                    out.write(f"mtllib {base_name}.mtl\n")
                
                for v in vertices:
                    out.write(f"v {v[0]} {v[1]} {v[2]}\n")
                
                if uvs:
                    for uv in uvs:
                        out.write(f"vt {uv[0]} {uv[1]}\n")
                
                for vn in normals:
                    out.write(f"vn {vn[0]} {vn[1]} {vn[2]}\n")
                
                if textures:
                    out.write(f"usemtl {base_name}\n")
                
                for a, b, c in faces:
                    if uvs:
                        out.write(f"f {a}/{a}/{a} {b}/{b}/{b} {c}/{c}/{c}\n")
                    else:
                        out.write(f"f {a}//{a} {b}//{b} {c}//{c}\n")
            
            print(f"✓ Wrote OBJ: {output_path}\n")
        except Exception as e:
            print("\n✖ ERROR writing OBJ file:", e)

if __name__ == "__main__":
    try:
        if len(sys.argv) <= 1:
            print("Drag .RIP files onto this script.")
            input("Press Enter to exit...")
            sys.exit()

        for arg in sys.argv[1:]:
            if os.path.isfile(arg):
                convert_rip_to_obj(arg)
            else:
                print(f"Skipping: {arg} (not a file)")

    except Exception as e:
        print("\n✖ CRITICAL ERROR – Converter crashed safely:")
        print(type(e).__name__, ":", e)
        traceback.print_exc()
        input("\nPress Enter to exit...")

    print("\nDone. Press Enter to exit.")
    input()
