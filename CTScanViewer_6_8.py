"""
Created By: George Lecakes
Version: 6.6
Additions:
	6.8 - UVW Transform added
	6.7 - Improved transfer GUI system added
	6.6 - Transfer function shader system added 
	6.5 - Gradient system added, updated GUI
	Annotation Module and Annotation tools of bone system
"""
import viz
#from BodyPlanes import *

viz.setOption( "viz.fullscreen.monitor", "1" )
viz.go( viz.FULLSCREEN )

#import BoundingBoxIntersection_V3 as BoundingBox
import Texture3DLoading as T3DLoading

from Tools import *
from ToolManager import *
from GUIs import *
from HistrogramTool import *
from GShader_Histogram_Gradient import *
from GShader_Histogram_Transfer import *
from Message import *

import Message_V2

from Annotations import AnnotationManager
from DataSet import *
import Gradient

import TransferFunction_V2 as TransferFunction

import math

import SponsorOverlay

import UVWTransform

sponsor_overlay = SponsorOverlay.SponsorOverlay( viz.addTexture('RowanLogos\\VRLabTitle.png') )

messageManager = MessageManager()

#Create shaders
shader_gradient = GShader_Histogram_Lighting()
shader_transfer = GShader_Transfer()

#data = dataHeadScanSpindles
data = dataFullBodyThresholded
#data = dataSiemensHighRes_Masked

#Create Volumetric Texture
textureList = T3DLoading.loadImages( data.imageDirectory )
texDescriptor = T3DLoading.VizTextureDescriptor()
texDescriptor.populateFromVizTexture( textureList[0] )
texDescriptor.imageType = viz.TEX_3D
texDescriptor.dimensions[2] = len( textureList )

blankTex3D = T3DLoading.createBlank3DTexture( texDescriptor )
T3DLoading.loadBlank3DTexture(blankTex3D, textureList)

#Transfer Function
transfer_function_manager = TransferFunction.TransferFunctionManager( data.name )

#Create Gradient 3D textures
gradientTex3D = None

#Do we have a gradient folder
if Gradient.CheckGradientFolder( data.imageDirectory):
	gradientList = T3DLoading.loadImages( data.imageDirectory + '\\' + Gradient.GRADIENTS_DIRECTORY_NAME )
	gradient_descriptor = T3DLoading.VizTextureDescriptor()
	gradient_descriptor.populateFromVizTexture( gradientList[0] )
	gradient_descriptor.imageType = viz.TEX_3D
	gradient_descriptor.dimensions[2] = len( gradientList )
	
	gradientTex3D = T3DLoading.createBlank3DTexture( gradient_descriptor )
	T3DLoading.loadBlank3DTexture( gradientTex3D, gradientList )

#Create Planes#
volume_region_extension = viz.addExtension('Extensions\\VizardExtension_VolumeRender.dle')
render_volume = volume_region_extension.addNode()

volume_region_extension.command( command = 0, x = data.bounding_box_size[0], y = data.bounding_box_size[1], z = data.bounding_box_size[2], w = 0.008 )
volume_region_extension.command( command = 1, x = 1, y = 0, z = 0)

print 'bounding box size', data.bounding_box_size

render_volume.texture( blankTex3D, unit = 0 )

render_volume.texture( gradientTex3D, unit = 1 )

#Apply texture
shader_transfer.ApplyShader( render_volume )

#Create clipping tool
clipPlaneTool = ClipPlaneTool( messageManager )
clipPlaneTool.addClipPlane( render_volume )

#Create histogram tool
data1 = HistogramData( data.imageDirectory )
#GrayHistTool =GrayHistogramTool( messageManager, data1, shader_texture)
#ColorHistTool = ColorHistogramTool( messageManager, data1, shader_texture)

#Create annotation tool
#annotationManager = AnnotationManager(messageManager)
#annotationManager.setScale( viz.Vector( 0.1, 0.1, 0.1 ) )

tool_manager = ToolManager(messageManager)


tool_manager.addTool( clipPlaneTool )
#tool_manager.addTool( annotationManager )

#resolution control
res_control = viz.addSlider()
res_control.ticksize(0.3, 0.6)
res_control.setPosition( 0.2, 0.025 )
res_control.set( 0.5 )
res_control_text = viz.addText("Resolution Control:", parent = viz.SCREEN)
res_control_text.setPosition(0.005, 0.0225)
res_control_text.scale( 0.1, 0.1, 0.1 )

#Gradient control
min_gradient_text = viz.addText("Gradient Minimum:", parent = viz.SCREEN)
min_gradient_text.setPosition(0.005, 0.0725)
min_gradient_text.scale( 0.1, 0.1, 0.1 )
min_gradient_control = viz.addSlider()
min_gradient_control.setPosition(0.2, 0.075)
min_gradient_control.set(0.0)
min_gradient_control.ticksize(0.3, 0.6)

max_gradient_text = viz.addText("Gradient Maximum:", parent = viz.SCREEN)
max_gradient_text.setPosition(0.005, 0.0475)
max_gradient_text.scale( 0.1, 0.1, 0.1 )
max_gradient_control = viz.addSlider()
max_gradient_control.setPosition(0.2, 0.05)
max_gradient_control.set(1.0)
max_gradient_control.ticksize(0.3, 0.6)

#Create controller
con = Controller(messageManager)

#Shader buttons
shader_radio_group = viz.addGroup()

lighting_shader_radio = viz.addRadioButton(parent = viz.SCREEN, group = shader_radio_group)
lighting_shader_radio.setScale(0.5, 0.5, 0.5)
lighting_shader_radio.setPosition(0.085, 0.975)

transfer_shader_radio = viz.addRadioButton(parent = viz.SCREEN, group = shader_radio_group)
transfer_shader_radio.setScale(0.5, 0.5, 0.5)
transfer_shader_radio.setPosition(0.085, 0.95)

lighting_shader_radio_text = viz.addText("Lighting Shader:", parent = viz.SCREEN)
lighting_shader_radio_text.setPosition(0.01, 0.975)
lighting_shader_radio_text.scale( 0.1, 0.1, 0.1 )
lighting_shader_radio_text.alignment( viz.ALIGN_LEFT_CENTER)

transfer_shader_radio_text = viz.addText("Transfer Shader:", parent = viz.SCREEN)
transfer_shader_radio_text.setPosition(0.01, 0.95)
transfer_shader_radio_text.scale( 0.1, 0.1, 0.1 )
transfer_shader_radio_text.alignment( viz.ALIGN_LEFT_CENTER)

#Enable light location
light_placement_button = viz.addButtonLabel(" Light Placement ", parent = viz.SCREEN)
light_placement_button.setScale( 0.3, 0.3, 0.3 )
light_placement_button.setPosition( 0.035, 0.925 )

LIGHT_PLACEMENT_FLAG = False

uvw_transform_manager = UVWTransform.UVWTransformManager(render_volume )

def loadState(state):
	tool_manager.loadState(state)
	
def onUpdate( updateNum ):
	vector = viz.MainView.getMatrix().getForward()
	volume_region_extension.command( command = 1, x = vector[0], y = vector[1], z = vector[2] * -1.0)

def onSlider( obj, pos ):
	multiplier = 1.0
	if obj == min_gradient_control:
		if data.gradient_multiplier:
			multiplier = data.gradient_multiplier
		GrayHistTool.shader.UpdateMinGradient(pos * multiplier)
		
	elif obj == max_gradient_control:
		if data.gradient_multiplier:
			multiplier = data.gradient_multiplier
		GrayHistTool.shader.UpdateMaxGradient(pos * multiplier)
	
	elif obj == res_control:

		total = pos * 0.01 + 0.0004
		
		volume_region_extension.command( command = 2, x = total)

def onMouseMove(button):
	global LIGHT_PLACEMENT_FLAG
	if LIGHT_PLACEMENT_FLAG:
		line = viz.mouse.getPosition()
		vector = (viz.Vector( line[0], line[1], 0.0 ) - viz.Vector(0.5, 0.5, 0.0)) * -1.0
		print vector
		
		
		'''
		distance = viz.Vector(viz.MainView.getPosition())
		distanceMag = math.sqrt(distance.x * distance.x + distance.y * distance.y + distance.z * distance.z)
		forwardVector = viz.Vector(viz.MainView.getMatrix().getForward()) * distanceMag
			
		lightDir = viz.Vector(line.begin) - forwardVector
		lightDir.normalize()
		print lightDir
		'''
		shader_gradient.UpdateLightDirection(vector)
		
def onMouseDown(button):
	global LIGHT_PLACEMENT_FLAG
	if button == viz.MOUSEBUTTON_LEFT and LIGHT_PLACEMENT_FLAG:
		LIGHT_PLACEMENT_FLAG = not LIGHT_PLACEMENT_FLAG
	

def onButton( obj,state):
	global LIGHT_PLACEMENT_FLAG
	
	if obj == lighting_shader_radio:
		print "lighting_shader_radio"
		current_tool = tool_manager.getCurrentTool()
		if isinstance(current_tool, HistogramTool):
			current_tool.SetShader(shader_gradient)
			shader_gradient.ApplyShader( render_volume )

	if obj == transfer_shader_radio:
		print "Transfer shader activated"
		#Apply texture
		shader_transfer.ApplyShader( render_volume )
		render_volume.texture( transfer_function_manager.transfer_texture.getVizardTexture() ,unit = 2)

	if obj == light_placement_button and state == viz.DOWN:
		print 'Toggle light button'
		LIGHT_PLACEMENT_FLAG = not LIGHT_PLACEMENT_FLAG
		
			
def onTransferFunctionUpdate( *args, **kwargs):
	pass
	


Message_V2.messageManager.subscribe( TransferFunction.TransferFunction_Messages.message_transfer_function_update, onTransferFunctionUpdate)


viz.callback( viz.TIMER_EVENT, onUpdate )
viz.callback( viz.SLIDER_EVENT, onSlider )
viz.callback( viz.BUTTON_EVENT, onButton )
viz.callback( viz.MOUSE_MOVE_EVENT, onMouseMove )
viz.callback( viz.MOUSEDOWN_EVENT, onMouseDown )
viz.starttimer( 0, 1.0, viz.PERPETUAL )