# ---------------------------------------------------------------------------
# NFT Collection Generator Script, by Guilherme 'Gulcasa' Santana
# 
# Creates an arbitrary number of images assembled from categorized parts
# Base .png image files must be collected in a folder, with subfolders for each of the layers (e.g. skin, lower clothing, upper clothing)
# Two .json rules files are used: rules.json dictates the possible choices for each layer (and their rarity), and banlist.json defines a "ban list", i.e. items that cannot be selected together due to clipping issues or just preference
# Both .json files were hand-written by me, but they can be just as easily partially automated with another script
# Most of the layer names and order decisions are arbitrary and hardcoded for my needs, but can be easily renamed or swapped around
#
# We use Pillow for image processing, and the 'choices' module of Random to determine the probability of each item being chosen
# Lastly, we also use Pickle to save and load the generated image hashes, so that we don't need to run this code for thousands of elements at once, which would take a long time
# Simply delete the generated "log.p" file to start a clean run, or change the _SEGMENTEDRUN constant to False to skip the logging completely
# Remember to adjust the PATH and BASEPATH constants to point to the correct folders, and set the number of images to be generated at TOTALIMGS
# ---------------------------------------------------------------------------

from PIL import Image
import pickle
import random
from random import choices
import json
import os
import time

# ------------- CONSTANTS -------------
_PATH = 'C:\\Users\\Gulcasa\\Documents\\GitHub\\character-art-generator\\files\\'
#_PATH = 'yourfilepath\\files\\'
#_BASEPATH = 'yourfilepath'
_BASEPATH = 'C:\\Users\\Gulcasa\\Documents\\GitHub\\character-art-generator\\'
_TOTALIMGS = 10
_SEGMENTEDRUN = True

_FACEDECORCHANCEA = 0.8
_FACEDECORCHANCEB = 0.2

# execution time tracker
start_time = time.time()

# ------------- FUNCTIONS -------------
# selects an element from a population list with the given weights
def SelectElement(population,weights,addToBanList):
    selectedElement = choices(population,weights)[0]
    # we repeat the selection step until we hit an item that isn't banned by a previous item
    while selectedElement in banList:
        selectedElement = choices(population,weights)[0]
        
     # finally, we search the ban list for the selected element, and append any banned items to the ban list
    if selectedElement in banData and addToBanList:
        for item in banData[selectedElement]:
            banList.append(item["object"])
            
    return selectedElement
    
# loads a given image in a folder, and pastes it over the current image combination
def PasteImage(imgName,folder,imgHash,skinTone = None):
    # we append the skin tone to the image name, if it has been passed
    if skinTone:
        imgName += ("-" + skinTone)
    imgFile =  Image.open(_PATH + folder + "\\" + imgName + ".png")
    img.paste(imgFile, (0,0), imgFile)
    return imgHash + imgName

print("--- Generating " + str(_TOTALIMGS) + " Images... ---")

# ------------- PROBABILITIES -------------
# loading and decoding the rules.json file
rulesfile = open(_BASEPATH + "rules.json")
rulesdata = json.load(rulesfile)

# loading and decoding the banlist.json file
banlistfile = open(_BASEPATH + "banlist.json")
banData = json.load(banlistfile)

# init population and weight lists
popBackground = list()
wghtBackground = list()
popBackeffects = list()
wghtBackeffects = list()
popBodybase = list()
wghtBodybase = list()
popClothing = list()
wghtClothing = list()
popClothacc = list()
wghtClothacc = list()
popEyes = list()
wghtEyes = list()
popFacedecor = list()
wghtFacedecor = list()
popHair = list()
wghtHair = list()
popHeaddecor = list()
wghtHeaddecor = list()
popMouths = list()
wghtMouths = list()
popToplayer = list()
wghtToplayer = list()
popUnderclothes = list()
wghtUnderclothes = list()
banList = list()

# filling the lists
for item in rulesdata['background']:
    popBackground.append(item["filename"])
    wghtBackground.append(item["chance"])
    
for item in rulesdata['back-effects']:
    popBackeffects.append(item["filename"])
    wghtBackeffects.append(item["chance"])
    
for item in rulesdata['body-base']:
    popBodybase.append(item["skin"])
    wghtBodybase.append(item["chance"])
    
for item in rulesdata['clothing']:
    popClothing.append(item["filename"])
    wghtClothing.append(item["chance"])
    
for item in rulesdata['cloth-acc']:
    popClothacc.append(item["filename"])
    wghtClothacc.append(item["chance"])
    
for item in rulesdata['eyes']:
    popEyes.append(item["filename"])
    wghtEyes.append(item["chance"])
    
for item in rulesdata['face-decor']:
    popFacedecor.append(item["filename"])
    wghtFacedecor.append(item["chance"])
    
for item in rulesdata['hair']:
    popHair.append(item["filename"])
    wghtHair.append(item["chance"])
    
for item in rulesdata['head-decor']:
    popHeaddecor.append(item["filename"])
    wghtHeaddecor.append(item["chance"])
    
for item in rulesdata['mouth']:
    popMouths.append(item["filename"])
    wghtMouths.append(item["chance"])
    
for item in rulesdata['top-layer']:
    popToplayer.append(item["filename"])
    wghtToplayer.append(item["chance"])
    
for item in rulesdata['under-clothes']:
    popUnderclothes.append(item["filename"])
    wghtUnderclothes.append(item["chance"])
    
# printing the element count, for debug/information purposes - uncomment as necessary
# totalCount = str((len(popBackground) + len(popBackeffects) + len(popClothacc) + len(popClothing) + len(popEyes) + len(popFacedecor) + len(popHair) + len(popHeaddecor) + len(popMouths) + len(popToplayer) + len(popUnderclothes)))
# print("--- Total element count: " + totalCount  + " ---")
# print("--- Backgrounds: " + str(len(popBackground))  + ", Back Effects: " + str(len(popBackeffects)) + ", Clothing Accessories: " + str(len(popClothacc)) + ", Clothing: " + str(len(popClothing)) + ", Eyes: " + str(len(popEyes)) + ", Face Decor: " + str(len(popFacedecor)) + ", Hair Styles: " + str(len(popHair)) + ", Head Decor: " + str(len(popHeaddecor)) + ", Mouth Styles: " + str(len(popMouths)) + ", Top Layer Effects: " + str(len(popToplayer)) + ", Under Clothing Accs: " + str(len(popUnderclothes)) + " ---")

# ------------- LOADING LOG -------------
curImg = 0
previousCount = 0
generatedImgHashes = list()

# if this will be a segmented run (a.k.a processing in chunks rather than the entire load at once), we check for the existence of a log file and load it
if(_SEGMENTEDRUN and os.path.exists(_BASEPATH + "log.p")):
    generatedImgHashes = pickle.load( open( _BASEPATH + "log.p", "rb" ) )
    previousCount = len(generatedImgHashes)
    curImg = previousCount

# ------------- GENERATION -------------
# we run the calculations and image assemblies X times, equal to the amount of images we want
while(curImg < (_TOTALIMGS + previousCount)):
    curImgHash = ""
    skin = ""
    
    # background
    choiceBackground = SelectElement(population=popBackground, weights=wghtBackground, addToBanList=False)
    curImgHash += choiceBackground
    img = Image.open(_PATH + "backgrounds\\" + choiceBackground + ".png")

    # back effects
    choiceBackeffect = SelectElement(population=popBackeffects, weights=wghtBackeffects, addToBanList=True)
    if(choiceBackeffect != "none"):
        curImgHash = PasteImage(choiceBackeffect,"back effects",curImgHash)

    # hair back
    choiceHair = SelectElement(population=popHair, weights=wghtHair, addToBanList=True)
     # not every hair style has a "hair back" image
    if(os.path.exists(_PATH + "hair backs\\hair-back-" + choiceHair + ".png")):
        curImgHash = PasteImage("hair-back-" + choiceHair,"hair backs",curImgHash)

    # body and skin
    skin = SelectElement(population=popBodybase, weights=wghtBodybase, addToBanList=True)
    curImgHash = PasteImage("body-shape-" + skin,"body base",curImgHash)
    curImgHash = PasteImage("head-shape-" + skin,"body base",curImgHash)
    
    # clothing  - decision step (it's selected before under clothes accessories, but applied after, to simplify the banlist)
    choiceClothing = SelectElement(population=popClothing, weights=wghtClothing, addToBanList=True)
    # if the item has "skin" in its name, we know it has an appended skin color attribute
    if "skin" in choiceClothing :
        choiceClothing = choiceClothing + "-" + skin
    
    # under clothes accessories
    choiceUnderclothes = SelectElement(population=popUnderclothes, weights=wghtUnderclothes, addToBanList=False)
    if(choiceUnderclothes != "none"):
        curImgHash = PasteImage(choiceUnderclothes,"under clothes accessories",curImgHash)
    
    # clothing - application step
    curImgHash = PasteImage(choiceClothing,"body clothing",curImgHash)

    # face shade (hair shading)
    if(os.path.exists(_PATH + "hair face shadow\\face-shade-" + choiceHair.split("-")[0] + "-" + skin + ".png")):
        curImgHash = PasteImage("face-shade-" + choiceHair.split("-")[0],"hair face shadow",curImgHash,skin)
        
    # mouth
    choiceMouth = SelectElement(population=popMouths, weights=wghtMouths, addToBanList=True)
    if(os.path.exists(_PATH + "mouths\\" + choiceMouth + "-" + skin + ".png")):
        curImgHash = PasteImage(choiceMouth,"mouths",curImgHash,skin)
        
    # eyes
    choiceEyes = SelectElement(population=popEyes, weights=wghtEyes, addToBanList=False)
    curImgHash = PasteImage(choiceEyes,"eyes",curImgHash)
    
    # face decor - _FACEDECORCHANCEA decided whether there will be any face decor at all, and _FACEDECORCHANCEB decides whether there will be a second face decor after the first
    if(random.random() <= _FACEDECORCHANCEA):
        choiceFacedecorA = SelectElement(population=popFacedecor, weights=wghtFacedecor, addToBanList=True)
        curImgHash = PasteImage(choiceFacedecorA,"face decor",curImgHash)
        
        if(random.random() <= _FACEDECORCHANCEB):
            choiceFacedecorB = SelectElement(population=popFacedecor, weights=wghtFacedecor, addToBanList=True)
            curImgHash = PasteImage(choiceFacedecorB,"face decor",curImgHash)
    
    # clothing accessories
    choiceClothingacc = SelectElement(population=popClothacc, weights=wghtClothacc, addToBanList=False)
    if(choiceClothingacc != "none"):
        curImgHash = PasteImage(choiceClothingacc,"clothing front accessories",curImgHash)
        
    # hair front - the hair has already been decided earlier, and we just use its identifier
    curImgHash = PasteImage("hair-front-" + choiceHair,"hair fronts",curImgHash)
    
    # head decor
    choiceHeadDecor = SelectElement(population=popHeaddecor, weights=wghtHeaddecor, addToBanList=False)
    if(choiceHeadDecor != "none"):
        curImgHash = PasteImage(choiceHeadDecor,"head decor",curImgHash)
    
    # top layer
    choiceToplayer = SelectElement(population=popToplayer, weights=wghtToplayer, addToBanList=False)
    if(choiceToplayer != "none"):
        curImgHash = PasteImage(choiceToplayer,"top layer effects",curImgHash)
    
    # final checks and generation
    if(curImgHash not in generatedImgHashes):
        generatedImgHashes.append(curImgHash)
        img.save(_BASEPATH + "output\\file" + str(curImg) + ".png")
        #img.show()
        curImg += 1
        
    # lastly, we clear the ban list after each execution, so that the next generation has a clean slate to work with
    banList.clear()

# if we're doing a segmented run, we'll save all of the generated hashes up to this point to the log file
if _SEGMENTEDRUN:
    pickle.dump( generatedImgHashes, open( _BASEPATH + "log.p", "wb" ) )

# printing final runtime, to get concerned at
print("--- Runtime: %s seconds ---" % ("{:.2f}".format(time.time() - start_time)))
