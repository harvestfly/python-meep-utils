#!/usr/bin/env python
#-*- coding: utf-8 -*-

## Import common moduli
import matplotlib, sys, os, time
import matplotlib.pyplot as plt
import numpy as np
from scipy.constants import c, hbar, pi

## Use LaTeX
matplotlib.rc('text', usetex=True)
matplotlib.rc('font', size=13)
matplotlib.rc('text.latex', preamble = '\usepackage{amsmath}, \usepackage{yfonts}, \usepackage{txfonts}, ')
plt.figure(figsize=(7,10))

# -- settings --
maxfreq = 4e12
frequnit = 1e12

plot_FFT = True
interp_anisotropy = 2e-5        # value lower than 1. interpolates rather vertically; optimize if plot desintegrates
FFTcutoff = 0.8    

plot_FDM = True
FDMtrunc = (.1, .5) 

plot_NRef = True


## Operate over multiple files
import sys
filenames = [x for x in sys.argv[1:] if ('-' not in x[0:1])]
Efs = []
Kzs = []
freqs = []
zfs = []

FDM_freqs = []
FDM_amplis = []
FDM_phases = []
FDM_Kzs = []
for filename, color in zip(filenames, matplotlib.cm.hsv(np.linspace(0,1,len(filenames)))): 
    Kz = None
    with open(filename) as datafile:
        for line in datafile:
            if line[0:1] in "0123456789": break         # end of file header
            value = line.replace(",", " ").split()[-1]  # the value of the parameter will be separated by space or comma
            if not Kz and ("Kz" in line): 
                Kz = float(value)
    (t, E) = np.loadtxt(filename, usecols=list(range(2)), unpack=True)

    if plot_FDM:
        #if True or '200' in filename:
            print filename
            import harminv_wrapper
            tscale = 3e9
            t1 = t[len(t)*FDMtrunc[0]:len(t)*FDMtrunc[1]]*tscale
            t1 -= np.min(t1)
            E1 = E[len(t)*FDMtrunc[0]:len(t)*FDMtrunc[1]]
            print np.max(t1)
            try:
                hi = harminv_wrapper.harminv(t1, E1, d=.1, f=15)
                hi['frequency'] *= tscale /frequnit
                hi['amplitude'] /= np.max(hi['amplitude'])
                hi['error'] /= np.max(hi['amplitude'])
                FDM_freqs = np.append(FDM_freqs,  hi['frequency'])
                FDM_amplis= np.append(FDM_amplis,  hi['amplitude'])
                FDM_phases= np.append(FDM_phases,  hi['phase'])
                FDM_Kzs   = np.append(FDM_Kzs,    Kz*np.ones_like(hi['frequency'])) 
            except: 
                print "Error: Harminv did not find any oscillator in "


    if plot_FFT:
        for field in (E,):
            field[t>max(t)*FFTcutoff] = field[t>max(t)*FFTcutoff]*(.5 + .5*np.cos(np.pi * (t[t>max(t)*FFTcutoff]/max(t)-FFTcutoff)/(1-FFTcutoff)))
        ## 1D FFT with cropping for useful frequencies
        freq    = np.fft.fftfreq(len(t), d=(t[1]-t[0]))         # calculate the frequency axis with proper spacing
        Ef      = np.fft.fft(E, axis=0) / len(t) * 2*np.pi     # calculate the FFT values
        truncated = np.logical_and(freq>0, freq<maxfreq)         # (optional) get the frequency range
        (Ef, freq) = map(lambda x: x[truncated], (Ef, freq))    # (optional) truncate the data points

        freq    = np.fft.fftshift(freq)
        Ef      = np.fft.fftshift(Ef)

        Kzs     = np.append(Kzs,    Kz*np.ones_like(freq))
        freqs   = np.append(freqs,  freq)
        Efs     = np.append(Efs,    Ef)




if plot_FFT:
    ## Interpolate 2D grid from scattered data
    from matplotlib.mlab import griddata
    fi = np.linspace(0, maxfreq/frequnit, 600)
    ki = np.linspace(0, np.max(Kzs), 200)

    ## Plot contours for gridded data
    if '-phase' in sys.argv[1:]:
        filesuffix = 'phase'

        z = griddata(Kzs*interp_anisotropy, freqs/frequnit, np.angle(Efs), ki*interp_anisotropy, fi, interp='nn')
        contours = plt.contourf(ki, fi, z, levels=np.linspace(-np.pi,np.pi,50), cmap=matplotlib.cm.hsv, extend='both') 
    else:
        filesuffix = 'ampli'

        z = griddata(Kzs*interp_anisotropy, freqs/frequnit, np.abs(Efs), ki*interp_anisotropy, fi, interp='nn')
        #log_min, log_max = np.log10(np.min(z)), np.log10(np.max(z))
        log_min, log_max = -5, .5
        levels = 10**(np.arange(         log_min,          log_max,  .2))       ## where the contours are drawn
        ticks  = 10**(np.arange(np.floor(log_min), np.ceil(log_max),  1))       ## where a number is printed
        contours = plt.contourf(ki, fi, z, levels=levels, cmap=plt.cm.gist_earth, norm = matplotlib.colors.LogNorm())
        plt.colorbar(ticks=ticks).set_ticklabels(['$10^{%d}$' % int(np.log10(t)) for t in ticks])



    for contour in contours.collections: contour.set_antialiased(False)     ## optional: avoid white aliasing (for matplotlib 1.0.1 and older) 


if plot_NRef:
    try:
        f, Nre = np.loadtxt('NRef.dat', usecols=(0,5), unpack=True)
        plt.plot(Nre*2*np.pi*f/2.998e8, f/frequnit, color='w', lw=2.5)
        plt.plot(-Nre*2*np.pi*f/2.998e8, f/frequnit, color='w', ls='--', lw=2.5)
    except IOError:
        print "File NRef.dat was not found - not plotting the curve for comparison"


if plot_FDM:
    c = plt.scatter(FDM_Kzs, FDM_freqs, s=FDM_amplis*10+1, c=FDM_phases, cmap=plt.cm.hsv, alpha=1)


## Simple axes
plt.ylim((0,4)); plt.yscale('linear')
plt.xlim((np.min(ki), np.max(ki))); plt.xscale('linear')

## ==== Outputting ====
## Finish the plot + save 
plt.xlabel(u"Wave vector [m$^{-1}$]"); 
plt.ylabel(u"Frequency [THz]"); 
plt.grid()
plt.legend(prop={'size':10}, loc='upper right')
plt.savefig("cdh_FDM_%s.png" % filesuffix, bbox_inches='tight')

    #plt.plot(freq, np.log10(np.abs(zf)+1e-10), color=color, label=u"$y'$", ls='-')      # (optional) plot amplitude
    #plt.plot(freq, np.unwrap(np.angle(zf)), color="#FF8800", label=u"$y'$", ls='--')   # (optional) plot phase

    ## FFT shift (to plot negative frequencies)
