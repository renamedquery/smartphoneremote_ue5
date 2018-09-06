import json

class Asset():
    """ glTF basic asset

    A asset can contain:
    - asset version
    """

    def __init__(self,*args, **kwargs):
        self.version = '2.0'

class Buffer():
    """ glTF basic buffer

    A buffer can contain:
    - byte byteLength
    - a URI pointing raw data
    """
    def __init__(self):
        self.byteLength = 0
        self.uri = ""

class BufferViews():
    """ glTF basic bufferViews

    A scene can contain:
    - an array of Node
    """
    def __init__(self):
        self.buffer = 0
        self.byteOffset = 0,
        self.byteLength = 0,
        self.byteStride = 0,
        self.target = ""

class Accessor():
    """glTF basic accessor"""
    def __init__(self):
        self.bufferView = 0
        self.byteOffset = 0
        self.type = "VEC2"
        self.componentType = 5126
        self.count = 2
        self.min = [0.0,0.0]
        self.max = [0.9,0.8]

class Primitive():
    """ glTF basic primitive

    A primitive can contain:
    - an array of Node
    """
    def __init__(self, *args, **kwargs):
        if 'mode' in kwargs:
            self.mode = kwargs['mode']
        if 'indices' in kwargs:
            self.indices = kwargs['indices']
        if 'attributes' in kwargs:
            self.attributes = kwargs['attributes']
        if 'material' in kwargs:
            self.material = kwargs['material']
        if 'target' in kwargs:
            self.target = kwargs['target']
        if 'weights' in kwargs:
            self.weights = kwargs['weights']


class Camera():
    """ glTF basic scenes

    A scene can contain:
    - an array of Node
    """
    def __init__(self):
        self.type = ''

class Mesh():
    """ glTF basic scenes

    A scene can contain:
    - an array of Node
    """
    def __init__(self, *args, **kwargs):
        if 'primitives' in kwargs:
            self.primitives = kwargs['primitives']
        else:
            self.primitives = []

        if 'name' in kwargs:
            self.name = kwargs['name']

class Scene(object):
    """ glTF basic scenes

    A scene can contain:
    - an array of Node
    """
    def __init__(self,json_scene = None):
        if json_scene is None:
            self.nodes = []
        else:
            self.nodes = json_scene['nodes']

class Node(object):
    """ glTF basic node

    A node can contains:
    - an array of indice of its children
    - a local transform
    - a mesh or a camera

    """
    def __init__(self, *args, **kwargs):
        if 'json_node' in kwargs:
            if 'children' in json_node:
                self.children = json_node['children']
            if 'matrix' in json_node:
                self.matrix = json_node['matrix']
            if 'mesh' in json_node:
                self.mesh = json_node['mesh']
            if 'camera' in json_node:
                self.camera = json_node['camera']

        else:
            if 'name' in kwargs:
                self.name = kwargs['name']
            if 'children' in kwargs:
                self.name = kwargs['children']
            if 'matrix' in kwargs:
                self.matrix = kwargs['matrix']
            if 'mesh' in kwargs:
                self.mesh = kwargs['mesh']

    def  __str__(self):
        return json.dumps(self, default=lambda o: o.__dict__,
            indent=4)

class glTF():
    """basic glTF file structure."""

    def __init__(self, path = None):
        self.asset = Asset()
        self.scene = 0
        self.scenes = []
        self.nodes = []
        self.meshes = []

        if path is not None:
            with open(path) as f:
                data = json.load(f)
                self.scene = data['scene']
                self.scenes = []
                self.nodes = []

                for s in data['scenes']:
                    self.scenes.append(Scene(s))

                for n in data['nodes']:
                    self.nodes.append(Node(n))



                # self.cameras = data['cameras']
                # self.meshes = data['meshes']
                # self.accessors = data['accessors']
                # self.bufferViews = data['bufferViews']
                # self.buffers = data['buffers']

    def find_node(self,node_name):
        for n in self.nodes:
            if n.name == node_name:
                return n


    def  __str__(self):
        return json.dumps(self, default=lambda o: o.__dict__,
            indent=4)

# class TNode():
#     def __init__(self, *args, **kwargs):
#         if 'childs' in kwargs:
#              self.child = kwargs['childs']
#         if 'parent' in kwargs:
#              self.child = kwargs['parent']
#         if 'name' in kwargs:
#              self.child = kwargs['name']
#
# class TTree():
#     def __init__(self, *args, **kwargs):
#         self.nodes = []
#
#     def find(name):
#         for n in self.nodes:
#             if n.name == name:
#                 return n

def b_load_mesh(obj):
    import array
    if obj.type == 'MESH':
        print("loading "+obj.name+" mesh")

        new_mesh = Mesh(name=obj.name+"_shape")
        attr = {}
        attr["POSITION"] = 1
        new_primitive  = Primitive(mode=4,attributes=attr, indices=0)
        indice_buffer = array.array('H')
        position_buffer = array.array('f')

        for triangle in obj.data.polygons:
                for vertex in triangle.vertices:
                    indice_buffer.append(vertex)
                    # print(obj.data.vertices[vertex].co)

        for vertex in obj.data.vertices:
            position_buffer.append(vertex.co.x)
            position_buffer.append(vertex.co.y)
            position_buffer.append(vertex.co.z)

        print(indice_buffer)
        print(len(indice_buffer)*indice_buffer.itemsize)
        print(position_buffer)
        print(len(position_buffer)*position_buffer.itemsize)

        geometry_buffer = indice_buffer.tobytes() + position_buffer.tobytes()
        print(len(geometry_buffer))
        file = open("test.bin", "wb")
        file.write(geometry_buffer)
        file.close()
        new_mesh.primitives.append(new_primitive)

        return new_mesh
    else:
        return -1


def load_blender(glft):
    import bpy, mathutils

    m = mathutils.Matrix()

    print("Exporting tree : ")
    glft.scene  = 0
    for scene in bpy.data.scenes:
        print("-"+scene.name)
        gltf_scene = Scene()

        #Fill node
        for obj in scene.objects:
            #print("--"+obj.name)
            #node = Node(obj.name)

            node = Node(name=obj.name)
            if obj.matrix_basis != m:
                node.matrix = MatrixToArray(obj.matrix_local)
            if obj.type == 'MESH':
                glft.meshes.append(b_load_mesh(obj))


            elif  obj.type == 'CAMERA':
                print("load camera")
                node.camera = 0


            gltf.nodes.append(node)

            if not obj.parent:
                gltf_scene.nodes.append(gltf.nodes.index(node))

        for obj in scene.objects:
            if obj.children:
                parent_node = glft.find_node(obj.name)
                parent_node.children = []

                for child in obj.children:
                    parent_node.children.append(glft.nodes.index(glft.find_node(child.name)))

        gltf.scenes.append(gltf_scene)

        file = open("test.gltf", "w", encoding="utf8", newline="\n")
        file.write(str(glft))
        file.write("\n")
        file.close()

def MatrixToArray(mat):
    array = []
    for r in mat.col:
        for i in r:
            array.append(i)

    return array


if __name__ == '__main__':
    import bpy

    bpy.ops.wm.open_mainfile(filepath="/home/slumber/Repos/DeviceTracking/examples/parent.blend")
    gltf = glTF()#'/home/slumber/Downloads/Duck.gltf')
    # gltf.scenes.append(Scene())
    # gltf.nodes.append(Node())
    load_blender(gltf)
    print(gltf)
