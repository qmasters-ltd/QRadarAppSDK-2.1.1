# Licensed Materials - Property of IBM
# 5725I71-CC011829
# (C) Copyright IBM Corp. 2015, 2020. All Rights Reserved.
# US Government Users Restricted Rights - Use, duplication or
# disclosure restricted by GSA ADP Schedule Contract with IBM Corp.

from tqdm import tqdm

class ProgressBar(tqdm):
    # There is no __init__ in this class, but that's how tqdm works.
    # pylint: disable=attribute-defined-outside-init
    def progress(self, bytes_transferred, total_bytes):
        self.total = int(total_bytes)
        self.update(int(bytes_transferred - self.n))
