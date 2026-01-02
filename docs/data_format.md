# data format specification

Data is stored in the pyarrow parquet format 

frame | integer | frame number starting from 0
person | integer | person id

*boundingbox* in video frame (in COCO format) ( y=0 is top of image)
x_min 
y_min
w
h

*pose estimation*
keypoints_2d | array of floats
keypoints_3d | array of floats
quats | array of floats

*pose assessment*
