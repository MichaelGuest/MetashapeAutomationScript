import Metashape

#Opens folder directory so you can specify path for exports
from tkinter import filedialog
from tkinter import *
root = Tk()
root.withdraw()
file_path = filedialog.askdirectory()

#Initializes psx file
doc = Metashape.app.document

#Creates a new chunk if and only if document doesn't have chunk already created
if len(doc.chunks):
    chunk = Metashape.app.document.chunk
else:
    chunk = doc.addChunk()

#Specifies Coordinate System
chunk.crs = Metashape.CoordinateSystem("EPSG::4326")

#Imports GPS data from photos
chunk.loadReferenceExif(load_accuracy=True)

#Gets relative atitude from image metadata and converts it to meters
for camera in chunk.cameras:
    if not camera.reference.location:
        continue
    if ("DJI/RelativeAltitude" in camera.photo.meta.keys()
        ) and camera.reference.location:
        z = float(camera.photo.meta["DJI/RelativeAltitude"])
        camera.reference.location = (camera.reference.location.x,
                                     camera.reference.location.y, z)

#Estimates images then disables images that are less than 0.5 quality
chunk.estimateImageQuality()

for i in range(0, len(chunk.cameras)):
    camera = chunk.cameras[i]
    quality = camera.frames[0].meta["Image/Quality"]
    if float(quality) < 0.5:
        camera.enabled = False

#Aligns all the photos
chunk.matchPhotos(
    accuracy=Metashape.HighAccuracy,
    generic_preselection=True,
    reference_preselection=True,
    keypoint_limit=60000,
    tiepoint_limit=0)
chunk.alignCameras(adaptive_fitting=True)
doc.save()

chunk.optimizeCameras(
    fit_f=True,
    fit_cx=True,
    fit_cy=True,
    fit_b1=True,
    fit_b2=False,
    fit_k1=True,
    fit_k2=True,
    fit_k3=True,
    fit_k4=False,
    fit_p1=True,
    fit_p2=True,
    fit_p3=False,
    fit_p4=False,
)
doc.save()

#Adjusts the ReconstructionUncertainty
f = Metashape.PointCloud.Filter()
f.init(chunk, criterion=Metashape.PointCloud.Filter.ReconstructionUncertainty)
f.removePoints(100)
f.removePoints(75)
f.removePoints(50)
f.removePoints(45)
f.removePoints(40)
f.removePoints(35)
f.removePoints(20)

chunk.optimizeCameras(
    fit_f=True,
    fit_cx=True,
    fit_cy=True,
    fit_b1=True,
    fit_b2=False,
    fit_k1=True,
    fit_k2=True,
    fit_k3=True,
    fit_k4=False,
    fit_p1=True,
    fit_p2=True,
    fit_p3=False,
    fit_p4=False,
)
doc.save()

#Adjusts the ProjectionAccuracy
f.init(chunk, criterion=Metashape.PointCloud.Filter.ProjectionAccuracy)
f.removePoints(3)
f.removePoints(2.8)
f.removePoints(2.5)
f.removePoints(2.3)

#sets tiepoint accuracy to 0.1
chunk.tiepoint_accuracy = 0.1

chunk.optimizeCameras(
    fit_f=True,
    fit_cx=True,
    fit_cy=True,
    fit_b1=True,
    fit_b2=True,
    fit_k1=True,
    fit_k2=True,
    fit_k3=True,
    fit_k4=True,
    fit_p1=True,
    fit_p2=True,
    fit_p3=True,
    fit_p4=True,
)

#Adjusts the Reprojection Error
f.init(chunk, criterion=Metashape.PointCloud.Filter.ReprojectionError)
f.removePoints(0.5)
f.removePoints(0.4)
f.removePoints(0.3)

chunk.optimizeCameras(
    fit_f=True,
    fit_cx=True,
    fit_cy=True,
    fit_b1=True,
    fit_b2=True,
    fit_k1=True,
    fit_k2=True,
    fit_k3=True,
    fit_k4=True,
    fit_p1=True,
    fit_p2=True,
    fit_p3=True,
    fit_p4=True,
)
doc.save()

#Builds the DenseCloud
chunk.buildDepthMaps(
    quality=Metashape.HighQuality,
    filter=Metashape.AggressiveFiltering,
    reuse_depth=True)
chunk.buildDenseCloud(point_colors=True)
doc.save()

#Builds 3D Model
chunk.buildModel(
    surface=Metashape.HeightField,
    interpolation=Metashape.EnabledInterpolation,
    source=Metashape.DenseCloudData,
    face_count=Metashape.HighFaceCount,
    vertex_colors=True,
    volumetric_masks=False,
    keep_depth=False)
doc.save()

#Decimates Model to 2000000 faces
chunk.decimateModel(face_count=200000)
doc.save()

#Builds Texture
chunk.buildUV(mapping=Metashape.AdaptiveOrthophotoMapping, count=1)
doc.save()
chunk.buildTexture(
    blending=Metashape.MosaicBlending,
    size=8192,
    fill_holes=True,
    ghosting_filter=True)
doc.save()

#Builds DEM
chunk.buildDem(
    source=Metashape.DenseCloudData,
    interpolation=Metashape.EnabledInterpolation,
    projection=Metashape.CoordinateSystem("EPSG::4326"))
doc.save()

#Builds Ortho
chunk.buildOrthomosaic(
    surface=Metashape.ElevationData,
    blending=Metashape.MosaicBlending,
    fill_holes=True,
    cull_faces=False,
    refine_seamlines=False,
    projection=Metashape.CoordinateSystem("EPSG::4326"))
doc.save()

#Exports PDF report to specified path
chunk.exportReport(
    path=file_path + "/exportedReport.pdf",
    title="Processing Report",
    page_numbers=True)

#Exports 3Dmodel PDF to specified path
chunk.exportModel(
    path=file_path + "/exportedModel.pdf",
    format=Metashape.ModelFormatPDF,
    texture_format=Metashape.ImageFormatJPEG,
    binary=True,
    precision=6,
    texture=True,
    normals=True,
    colors=True,
    colors_rgb_8bit=True,
    cameras=True,
    markers=True,
    udim=False,
    alpha=False,
    raster_transform=Metashape.RasterTransformNone)

#Exports 3Dmodel KMZ to overlay on Google Earth
def export3Dkmz():
    chunk.exportModel(
        path=file_path + "/exportedModel.kmz",
        format=Metashape.ModelFormatKMZ,
    )

export3Dkmz()

#Exports DEM KML & TIFF to specified path
chunk.exportDem(
    path=file_path + "/exportedDem.tif",
    projection=Metashape.CoordinateSystem("EPSG::4326"),
    raster_transform=Metashape.RasterTransformPalette,
    write_kml=True,
    write_world=True,
    write_scheme=False,
    tiff_big=False,
    tiff_tiled=False,
    tiff_overviews=True)

#Exports Orthomosaic KMZ to overlay on Google Earth
def exportDemkmz():
    chunk.exportDem(
        path=file_path + "/exportedDem.kmz",
        format=Metashape.RasterFormatKMZ,
    )

exportDemkmz()

#Exports Ortho KML & TIFF to specified path
chunk.exportOrthomosaic(
    path=file_path + "/exportedOrthomosaic.tif",
    projection=Metashape.CoordinateSystem("EPSG::4326"),
    raster_transform=Metashape.RasterTransformNone,
    white_background=True,
    write_kml=True,
    write_world=True,
    tiff_big=False,
    tiff_tiled=False,
    tiff_overviews=True,
    tiff_compression=Metashape.TiffCompressionJPEG,
    jpeg_quality=70,
    write_alpha=True)


#Exports Orthomosaic KMZ to overlay on Google Earth
def exportOrthomosaickmz():
    chunk.exportOrthomosaic(
        path=file_path + "/exportedOrthomosaic.kmz",
        format=Metashape.RasterFormatKMZ,
    )

exportOrthomosaickmz()

print("You can go eat pizza now!")
