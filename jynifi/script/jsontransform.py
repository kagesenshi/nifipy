# JSON Transformation DSL for NiFi
#
# Variables:
#
# * transformRule
# * outputSkeleton
#

import json
import copy
import yaml
import imp
import os
from org.apache.commons.io import IOUtils
from java.nio.charset import StandardCharsets
from org.apache.nifi.processor.io import StreamCallback
from rulez.transformer import Engine


class TransformCallback(StreamCallback):

    def __init__(self, engine, rule, dest):
        self.engine = engine
        self.rule = rule
        self.dest = copy.deepcopy(dest)

    def process(self, inputStream, outputStream):
        src = json.loads(IOUtils.toString(inputStream, StandardCharsets.UTF_8))
        dest = self.engine.remap(self.rule, src, self.dest)
        outputStream.write(json.dumps(dest))


def jsontransform(session, REL_SUCCESS, REL_FAILURE, transformRule,
        outputSkeleton, extensionModules):


    mods = []
    for m in extensionModules.getValue().split(','):
        n = os.path.basename(m)[:-2]
        mods.append(imp.load_source(n, m))
    
    if not Engine.is_committed():
        Engine.commit()
    
    rule = yaml.load(transformRule.getValue())
    skel = outputSkeleton.getValue()
    if skel.startswith('file://'):
        dest = json.loads(open(skel[7:]).read())
    else:
        dest = json.loads(skel)

    tc = TransformCallback(Engine(), rule, dest)
    ff = session.get()
    session.write(ff, tc)
    session.transfer(ff, REL_SUCCESS)
