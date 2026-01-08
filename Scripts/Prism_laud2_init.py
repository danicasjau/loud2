 # -*- coding: utf-8 -*-
#
####################################################
#
# PRISM - Pipeline for animation and VFX projects
#
# www.prism-pipeline.com
#
# contact: contact@prism-pipeline.com
#
####################################################
#
#
# Copyright (C) 2016-2023 Richard Frangenberg
# Copyright (C) 2023 Prism Software GmbH
#
# Licensed under GNU LGPL-3.0-or-later
#
# This file is part of Prism.

from Prism_laud2_Variables import Prism_laud2_Variables
from Prism_laud2_Functions import Prism_laud2_Functions


class Prism_laud2(Prism_laud2_Variables, Prism_laud2_Functions):
    def __init__(self, core):
        Prism_laud2_Variables.__init__(self, core, self)
        Prism_laud2_Functions.__init__(self, core, self)


