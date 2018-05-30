from astro.locales import mtlemmon
from rts2solib import focusobs
from astro.angles import Deg10


m=mtlemmon()

count=0
for alt in [70]:
    for az in range(0, 360, 60):
        ra, dec= m.hor2eq(Deg10(alt), Deg10(az))
        rastr, decstr=ra.Format('hours'), dec.Format('degarc180')
        focusobs(name="focus{:02d}".format(count), ra=rastr, dec=decstr)
        count+=1
        












