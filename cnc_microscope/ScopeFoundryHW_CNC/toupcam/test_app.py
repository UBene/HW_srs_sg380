from toupcam.camera import ToupCamCamera, get_number_cameras
import time

print('num cams', get_number_cameras())
cam = ToupCamCamera(resolution=5, cam_index=0)
print
cam.open()
time.sleep(1)

im = cam.get_pil_image()

print(im.size)

print(cam.get_exposure_time())

cam.save('C:/data/_test/foo.jpg')