import sys, os
from urdfpy import URDF
import subprocess
import numpy as np
import trimesh
import re

def main(argv):
    if (len(argv) < 2) :
        print("No file path specified or urdf as first argument.")
        print("No name given for saved files as second argument.")
        print("python3 urdf.py [XARCO_FILE_PATH] [NAME]")
        print("                        ^                 ^")
    elif (len(argv) < 3) :
        if (argv[1] == "-h") :
            print("Usage: python3 urdf.py [XARCO_FILE_PATH] [NAME]")
            print("")
            print("Process URDF file and save it as [NAME] in the local directory.")
            print("Show 3D model dynamically and save an image as [NAME].png of a chosen view and the 3D model as [NAME].stl file also in the local directory.")
        else :
            print("No name given for saved files as second argument.")
            print("python3 urdf.py [XARCO_FILE_PATH] [NAME]")
            print("                                          ^")
    else :
        xacro = "echo $(xacro "+os.path.abspath(argv[1])+")"
        xacroProcess = subprocess.run(xacro,shell=True,stdout=subprocess.PIPE)
        xacroOutput = str(xacroProcess.stdout)[2:-3]
        print(xacroOutput)
        print("")
        print("Press ENTER to process URDF")

        packages = np.unique(np.array([xacroOutput[int(m.start()):int(m.end())] for m in re.finditer('package://[a-zA-Z_]+/', xacroOutput)]))

        for package in packages:
            rosFind = "rospack find " + package.split("/")[-2]
            rosFindProcess = subprocess.run(rosFind,shell=True,stdout=subprocess.PIPE)
            rosFindOutput = str(rosFindProcess.stdout)[2:-3] + "/" 
            xacroOutput = xacroOutput.replace(package,rosFindOutput)

        xacroOutput = xacroOutput.replace("file://","")

        input()

        URDFfile = open(os.path.dirname(__file__)+argv[2]+".urdf", "w")
        URDFfile.write(xacroOutput)
        URDFfile.close()

        from urdfpy import URDF

        scene = trimesh.Scene()
        cfg = {
            'front_left_wheel': 0.0,
            'front_right_wheel': 0.0,
            'rear_left_wheel': 0.0,
            'rear_right_wheel': 0.0}
        cfg_trajectory = {
            'front_left_wheel': [-np.pi, np.pi],
            'front_right_wheel': [-np.pi, np.pi],
            'rear_left_wheel': [-np.pi, np.pi],
            'rear_right_wheel': [-np.pi, np.pi]
        }

        robot = URDF.load(os.path.dirname(__file__)+argv[2]+".urdf")

        print("")
        print("List of joints that can be articulated:")
        for joint in robot.actuated_joints:
            print("    "+joint.name)

        #robot.show(cfg=cfg)
        #robot.animate(cfg_trajectory=cfg_trajectory)

        meshes = robot.visual_trimesh_fk(cfg=cfg)

        mesh = trimesh.Trimesh()

        for submesh in meshes:
            pose = meshes[submesh]
            submesh.apply_transform(pose)
            mesh = trimesh.util.concatenate([mesh,submesh])

        newColors = np.array(mesh.visual.face_colors)
        newColors[:,-1] = 150

        mesh.visual = trimesh.visual.create_visual(face_colors=newColors, mesh=mesh)
        scene.add_geometry(mesh)

        scene.set_camera((np.pi/3,0.0,3*np.pi/4),3.5,(0,0,0.5))
        scene.show()
        data = scene.save_image()
        from PIL import Image
        rendered = Image.open(trimesh.util.wrap_as_stream(data))
        rendered.save(os.path.dirname(__file__)+argv[2]+".png")

        stl = trimesh.exchange.stl.export_stl_ascii(mesh)
        STLfile = open(os.path.dirname(__file__)+argv[2]+".stl", 'w')
        STLfile.write(str(stl))
        STLfile.close()

if __name__ == "__main__":
	main(sys.argv)
