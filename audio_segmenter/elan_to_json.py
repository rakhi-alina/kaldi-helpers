#!/usr/bin/python3

import xml.etree.ElementTree as ET
import sys, json, glob, re

RepositoryPath                  = "/Volumes/FLASH DRIVE" # Repository home drive

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# EAF: parse elan file and extract information from it for json
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
class EAF:
  def __init__(self, path):
    self.Tree                   = ET.parse(path)
    self.Root                   = self.Tree.getroot()
    self.getURI()
    self.getTimes()
    self.getAlignable()
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # get the URI of a .wav or .mp3 media file and find the file in the repository with
  # the same name
  def getURI(self):
    # <MEDIA_DESCRIPTOR MEDIA_URL="file:///Volumes/etha/morehead aufnahmen - FERTIG/2010 09 05 - kukufia/tci20100905CDa-louder.wav" MIME_TYPE="audio/x-wav"/>
    self.AudioFilename          = ""
    for media in self.Root.iter("MEDIA_DESCRIPTOR"):
      filename                  = media.get("MEDIA_URL")
      filename                  = filename.split("/")[-1]
      if not re.match('^.*\.(wav|mp3)$',filename.lower()): continue
      if filename: filepattern  = RepositoryPath+'/**/'+filename
      filepaths                 = glob.glob(filepattern, recursive=True)
      self.AudioFilename        = "|".join( map(lambda x: "."+x[len(RepositoryPath):], filepaths) )
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # get the time point to time (milliseconds) mapping
  def getTimes(self):
    self.TimeCodes              = {}
    for time in self.Root.iter('TIME_SLOT'): # TIME_SLOT_ID="ts33" TIME_VALUE="31580"
      t, tv                     = time.get("TIME_SLOT_ID"), time.get("TIME_VALUE")
      if not tv: tv             = -1
      self.TimeCodes[t]         = int(tv)
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # parse the alignable and referred annotations
  def getAlignable(self):
    self.Alignable              = {}
    for tier in self.Root.iter('TIER'):
      participant, tierN        = tier.get('PARTICIPANT'), tier.get('TIER_ID')
      for aa in tier.iter('ALIGNABLE_ANNOTATION'): # TIME_SLOT_ID="ts33" TIME_VALUE="31580"
        a,t1,t2                 = aa.get("ANNOTATION_ID"),aa.get("TIME_SLOT_REF1"),aa.get("TIME_SLOT_REF2")
        avs                     = list( map(lambda a: a.text, list( aa.iter('ANNOTATION_VALUE') )) )
        if avs and avs[0]: strg   = "|".join( avs )
        else: strg              = ""
        self.Alignable[a]       = (participant,tierN,strg,self.TimeCodes[t1],self.TimeCodes[t2])
    for tier in self.Root.iter('TIER'):
      participant, tierN        = tier.get('PARTICIPANT'), tier.get('TIER_ID')
      for aa in tier.iter('REF_ANNOTATION'): # ANNOTATION_ID="a626" ANNOTATION_REF="a1"
        a,ar                    = aa.get("ANNOTATION_ID"),aa.get("ANNOTATION_REF")
        t1,t2                   = self.Alignable[ar][3],self.Alignable[ar][4]
        avs                     = list( map(lambda a: a.text, list( aa.iter('ANNOTATION_VALUE') )) )
        if avs and avs[0]: strg   = "|".join( avs )
        else: strg              = ""
        # print("Storing %s,%s" % (a,tierN))
        self.Alignable[a]       = (participant,tierN,strg,t1,t2)
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # Write json for each annotation
  def jsonList(self):
    # ts                          = list(self.TimeCodes.keys())
    # ts.sort()
    # strg                        = ""
    # for t in ts: strg          += "%s: %d\n" % (t, self.TimeCodes[t])
    #
    ass                         = list(self.Alignable.keys())
    ass.sort()
    myjson                      = []
    for a in ass:
      al                        = list(self.Alignable[a])
      if al[3] == -1: al[3]     = al[4]
      if al[4] == -1: al[4]     = al[3]
      myjson.append({
        "audioFilename": self.AudioFilename,
        "speakerId": al[0],
        "tier": al[1],
        "transcript": al[2],
        "startMs": al[3],
        "stopMs": al[4],
        "aCode": a
      })
    return myjson

jsons                           = []
for fpath in glob.iglob(RepositoryPath+'/**/*.eaf', recursive=True):
  print("%s starts" % (fpath),file=sys.stderr)
  eaf                           = EAF(fpath)
  jsons                        += eaf.jsonList()
print( json.dumps(jsons,indent=2) )
