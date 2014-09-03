import numpy as np
import pysam
import gzip

MIN_MAP_QUAL = 10
MAX_VAL = 65535

class ZipFile():

    def __init__(self, filename):

        if os.path.isfile(filename):
            pipe = subprocess.Popen(["zcat", filename], stdout = subprocess.PIPE)
            self.handle = pipe.stdout
            # remove header
            header = self.handle.next()
        else:
            raise IOError

    def _readline(self):

        for line in self.handle:
            yield tuple(line.strip().split('\t'))

    def read(self, batch=None):

        if batch is None:
            # read the whole file
            locations = [line for line in self._readline()]
        else:
            # read a chunk of the file
            locations = [self.handle.next().strip().split('\t') \
                for index in xrange(chunk)]

        for loc in locations:
            loc[1] = int(loc[1])
            loc[2] = int(loc[2])

        return locations


class BamFile():

    def __init__(self, filename):

    	self._handle = pysam.Samfile(filename, "rb")

    def get_read_counts(self, locations, width=200):

    	counts = []
    	filtered_locations = []
    	scores = []

    	for location in locations:

    		chrom = location[0]
    		strand = location[3]
    		if strand=='+':
    			center = location[1]
    		else:
    			center = location[2]
    		left = center-width/2
    		right = center+width/2

    		sam_iter = self._handle.fetch(reference=chrom, start=left, end=right)
    		forward = np.zeros((width,), dtype=np.uint)
    		reverse = np.zeros((width,), dtype=np.uint)

    		for read in sam_iter:

                # skip read if unmapped
    			if read.is_unmapped:
    				continue

                # skip read, if mapping quality is low
    			if read.mapq < MIN_MAP_QUAL:
    				continue

    			start = read.pos
				end = start + read.alen

                # skip read, if both ends don't fall within window
                if start < left or end >= right:
                    continue

				if read.is_reverse:
					reverse[end-left] += 1
				else:
					forward[start-left] += 1

            # flip fwd and rev strand reads, 
            # if the motif is on the opposite strand.
            if strand=='+':
                count = np.hstack((forward, reverse))
            else:
                count = np.hstack((reverse[::-1], forward[::-1]))

            count[count>MAX_VAL] = MAX_VAL
    		counts.append(count.astype(np.uint16))

        counts = np.array(counts)
        return counts

    def close(self):

        self._handle.close()
