#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# create new version of shape(s) and fix all files:
#
# 1. Determine Dependencies: Find all places where a shape is referred to
#    Alias Shapes will receive a new version as well -> Add to version list, determine dependencies as well
# 2. Build mapping table [old]=>[new], such as CDClass_V002 => CDClass_V003
# 3. Copy old version to old/ folder: cp [old].xml old/[old].xml
# 4. Rename shape files using git: git mv [old].xml [new].xml
# 5. Fix [new].xml files: 
#       <Shape id="[old]" ...> => <Shape id="[new]" ...> 
#       <Shortcut ... to="[old]"> => <Shortcut ... to="[new]"> 
# 6. Fix old/[old].xml files: 
#       <Shape ...> => <Shape ... system="true"> 
# 7. Fix collections (Definition.[collection].xml):
#       Identify includes with changed version
#       Replace old with new:
#         <!-- include includes/shapes/[old].xml -->  => <!-- include includes/shapes/[new].xml --> 
#       Append old version:
#         <!-- old versions to keep compatibility ( invisible ) -->
#           <!-- include includes/shapes/old/[old].xml -->
import os
import re
import glob
import shutil

S_DEBUG=True

S_DEFINITIONS_DIR = "src"
S_SHAPE_PATH = "src/includes/shapes"
S_DEFINITIONS_SRC_FILENAME_RE = "Definition\.([^.]+)\.xml"
S_FILE_INCLUDE_RE = "<!-- include ([^ ]+) -->"
S_SHAPE_ID='<Shape'
S_SHAPE_ID_RE='<Shape.*id="([^"]+)".*>'
S_SHORTCUT_TO='<Shortcut'
S_SHORTCUT_TO_RE='<Shortcut.*to="([^"]+)".*>'

# Map shapes
dShapeMap = {
    "ADEndOfActivity_V001" : "ADEndOfActivity_V002",
    "ADEndOfFlow_V001" : "ADEndOfFlow_V002",
    "ADStartOfActivity_V001" : "ADStartOfActivity_V002",
    "AnnDots_V001" : "AnnDots_V002",
    "SDStartState_V001" : "SDStartState_V002",
    "SDEndState_V001" : "SDEndState_V002",
    "SeqDSequenceDiagram_V001" : "SeqDSequenceDiagram_V001"
}

dShapeMap1 = {
    "ADAction_V001" : "ADAction_V002",
    "ADDecision_V001" : "ADDecision_V002", 
    "ADFlowHorizontalLoopB_V001" : "ADFlowHorizontalLoopB_V002", 
    "ADFlowHorizontalLoopT_V001" : "ADFlowHorizontalLoopT_V002", 
    "ADFlowHorizontalMulti_V001" : "ADFlowHorizontalMulti_V002", 
    "ADFlowVertical_V001" : "ADFlowVertical_V002", 
    "ADFlowVerticalMulti_V001" : "ADFlowVerticalMulti_V002", 
    "ADForkJoin_V001" : "ADForkJoin_V002", 
    "ADLaneMultiVertical_V001" : "ADLaneMultiVertical_V002", 
    "AllDDirectLine_V001" : "AllDDirectLine_V002", 
    "AllDHorVertLine_V001" : "AllDHorVertLine_V002", 
    "AllDRoundedRectangle_V001" : "AllDRoundedRectangle_V002", 
    "AnnArrowDirectDashed_V001" : "AnnArrowDirectDashed_V002", 
    "AnnCurlyBracketVertical_V001" : "AnnCurlyBracketVertical_V002", 
    "AnnGroupCFA_V001" : "AnnGroupCFA_V002", 
    "AnnLane_V001" : "AnnLane_V002", 
    "AnnLaneHorizontal_V001" : "AnnLaneHorizontal_V002", 
    "AnnLegend_V001" : "AnnLegend_V002", 
    "AnnLineDirect_V001" : "AnnLineDirect_V002", 
    "AnnLineHorizontalMulti_V001" : "AnnLineHorizontalMulti_V002", 
    "AnnLineVerticalMulti_V001" : "AnnLineVerticalMulti_V002", 
    "AnnNote_V001" : "AnnNote_V002", 
    "AnnPlainText_V001" : "AnnPlainText_V002", 
    "AnnRectangle_V001" : "AnnRectangle_V002", 
    "AnnRectangleRounded_V001" : "AnnRectangleRounded_V002", 
    "BDAccess_V001" : "BDAccess_V002", 
    "BDAccessHorizontal_V001" : "BDAccessHorizontal_V002", 
    "BDAccessHorizontalMulti_V001" : "BDAccessHorizontalMulti_V002", 
    "BDAccessRW_V001" : "BDAccessRW_V002", 
    "BDAccessRWCurvedVertical_V001" : "BDAccessRWCurvedVertical_V002", 
    "BDAccessVertical_V001" : "BDAccessVertical_V002", 
    "BDAccessVerticalMulti_V001" : "BDAccessVerticalMulti_V002", 
    "BDAgent_V001" : "BDAgent_V002", 
    "BDChannel_V001" : "BDChannel_V002", 
    "BDChannelHorizontal_V001" : "BDChannelHorizontal_V002", 
    "BDChannelHorizontalMulti_V001" : "BDChannelHorizontalMulti_V002", 
    "BDChannelVertical_V001" : "BDChannelVertical_V002", 
    "BDChannelVerticalMulti_V001" : "BDChannelVerticalMulti_V002", 
    "BDCircularAccessRW_V001" : "BDCircularAccessRW_V002", 
    "BDHumanAgent_V001" : "BDHumanAgent_V002", 
    "BDLAccess_V001" : "BDLAccess_V002", 
    "BDLChannel_V001" : "BDLChannel_V002", 
    "BDModAccessHorizontal_V001" : "BDModAccessHorizontal_V002", 
    "BDModAccessVertical_V001" : "BDModAccessVertical_V002", 
    "BDRoundStorage_V001" : "BDRoundStorage_V002", 
    "BDSAccess_V001" : "BDSAccess_V002", 
    "BDSChannel_V001" : "BDSChannel_V002", 
    "BDStorage_V001" : "BDStorage_V002", 
    "BDStraightArrow_V001" : "BDStraightArrow_V002", 
    "BDStraightArrowHorizontal_V001" : "BDStraightArrowHorizontal_V002", 
    "BDUAgent_V001" : "BDUAgent_V002", 
    "BDUStorage_V001" : "BDUStorage_V002", 
    "CDAssociationHorizontal_V002" : "CDAssociationHorizontal_V003", 
    "CDAssociationHorizontalMulti_V002" : "CDAssociationHorizontalMulti_V003", 
    "CDAssociationVertical_V002" : "CDAssociationVertical_V003", 
    "CDAssociationVerticalMulti_V002" : "CDAssociationVerticalMulti_V003", 
    "CDClass_V002" : "CDClass_V003", 
    "CDClassSimple_V002" : "CDClassSimple_V003", 
    "CDSpecializationHorizontalMulti_V002" : "CDSpecializationHorizontalMulti_V003", 
    "CDSpecializationVerticalMulti_V002" : "CDSpecializationVerticalMulti_V003", 
    "SDState_V001" : "SDState_V002", 
    "SDTransitionHorizontal_V001" : "SDTransitionHorizontal_V002", 
    "SDTransitionHorizontalMulti_V001" : "SDTransitionHorizontalMulti_V002", 
    "SDTransitionVertical_V001" : "SDTransitionVertical_V002", 
    "SDTransitionVerticalMulti_V001" : "SDTransitionVerticalMulti_V002", 
    "SeqDAgentLifeline_V001" : "SeqDAgentLifeline_V002", 
    "SeqDAsyncMessageExchange_V001" : "SeqDAsyncMessageExchange_V002", 
    "SeqDCombinedFragment_V001" : "SeqDCombinedFragment_V002", 
    "SeqDCreateInstance_V001" : "SeqDCreateInstance_V002", 
    "SeqDSyncMessageExchange_V001" : "SeqDSyncMessageExchange_V002", 
    "SeqDSyncSelfMessageExchange_V001" : "SeqDSyncSelfMessageExchange_V002" ,
    "ADFlow_V001" : "ADFlowVertical_V002", 
    "SeqDLifeline_V001" : "SeqDAgentLifeline_V002"
}
lNewShapes = dShapeMap.values()
lOldShapes = dShapeMap.keys()

# Fix new files
for sNewShape in lNewShapes:
    sNewShapeFilename = sNewShape + ".xml"
    # check whether file exists
    if os.path.isfile(os.path.join(S_SHAPE_PATH, sNewShapeFilename)):
        bModified = False
        with open(os.path.join(S_SHAPE_PATH, sNewShapeFilename), "r", encoding="utf-8") as newShapeFileHandler:
            if S_DEBUG:
                print(">> open " + os.path.join(S_SHAPE_PATH, sNewShapeFilename))
            
            sFirstLine = newShapeFileHandler.readline()
            if S_DEBUG:
                print("Line 1=" + sFirstLine)
            sNewFirstLine = sFirstLine
            erg = re.search(S_SHAPE_ID_RE, sFirstLine)
            if erg:
                # found a <Shape id="" > Pattern
                sShapeID = erg.group(1)
                if S_DEBUG:
                    print("<Shape id=" + sShapeID)
                if sShapeID in dShapeMap:
                    sNewFirstLine = sFirstLine.replace(sShapeID, dShapeMap[sShapeID])
                    bModified = True
                    if S_DEBUG:
                        print("=> " + sNewFirstLine)
            else:
                erg = re.search(S_SHORTCUT_TO_RE, sFirstLine)
                if erg:
                    # found a <Shortcut to="" > Pattern
                    sShapeID = erg.group(1)
                    if S_DEBUG:
                        print("<Shortcut to=" + sShapeID)
                    if sShapeID in dShapeMap:
                        sNewFirstLine = sFirstLine.replace(sShapeID, dShapeMap[sShapeID])
                        bModified = True
                        if S_DEBUG:
                            print("=> " + sNewFirstLine)
            if bModified:
                # Read file content 
                sShapeLinesRest = newShapeFileHandler.readlines()
                sShapeLines = [ sNewFirstLine ]
                sShapeLines.extend(sShapeLinesRest)
        if bModified:
            with open(os.path.join(S_SHAPE_PATH, sNewShapeFilename), "w", encoding="utf-8") as newShapeFileHandler:
                if S_DEBUG:
                    print(">> write modified version of " + os.path.join(S_SHAPE_PATH, sNewShapeFilename))
                newShapeFileHandler.writelines(sShapeLines)

# Fix old files                
