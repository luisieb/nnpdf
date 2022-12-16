"""Script that calls fiatlux to add the photon PDF."""
import lhapdf
import fiatlux
import numpy as np
from eko.output.legacy import load_tar
from eko.interpolation import XGrid
from eko.output.manipulate import xgrid_reshape
from eko.interpolation import make_grid
from .structure_functions import StructureFunction
from scipy.interpolate import interp1d
from scipy.integrate import trapezoid

import yaml
from os import remove

class Photon:
    def __init__(self, theoryid, fiatlux_runcard, replica=0):
        # TODO : for the moment we do the 0-th replica then we change it
        self.theory = theoryid.get_description()
        self.fiatlux_runcard = fiatlux_runcard
        if fiatlux_runcard is not None:
            self.q_in2 = 100**2
            self.alpha_em_ref = self.theory["alphaqed"]
            self.qref = self.theory["Qref"]
            self.eu2 = 4. / 9
            self.ed2 = 1. / 9
            self.eq2 = [self.ed2, self.eu2, self.ed2, self.eu2, self.ed2, self.eu2] # d u s c b t
            self.set_thresholds_a_em()

            self.qcd_pdfs = lhapdf.mkPDF(fiatlux_runcard["pdf_name"], replica)
            path_to_F2 = fiatlux_runcard["path_to_F2"]
            path_to_FL = fiatlux_runcard["path_to_FL"]
            f2 = StructureFunction(path_to_F2, self.qcd_pdfs)
            fl = StructureFunction(path_to_FL, self.qcd_pdfs)

            # lux = fiatlux.FiatLux(fiatlux_runcard)
            # we have a dict but fiatlux wants a yaml file
            # TODO : remove this dirty trick
            ff = open('fiatlux_runcard.yml', 'w+')
            yaml.dump(self.fiatlux_runcard, ff)
            self.lux = fiatlux.FiatLux('fiatlux_runcard.yml')
            remove('fiatlux_runcard.yml')
            self.lux.PlugAlphaQED(self.alpha_em, self.qref)            
            self.lux.PlugStructureFunctions(f2.FxQ, fl.FxQ, self.F2LO)
            self.lux.InsertInelasticSplitQ([4.18, 1e100])

            self.produce_interpolator()

    # since we interpolate this is useless now
    def exctract_grids(self, xgrids):
        r"""
        Extract the subgrids inside xgrids.

        xgrids is the concatenation of different grids, i.e.
        xgrid = np.array([xmin1, ..., xmax1, xmin2, ...,xmax2, xmin3, ...]).
        The different grids are extracted and stored in a list:
        xgrid_list = [np.array([xgrid1]), np.array([xgrid2]), ...]

        Parameters
        ----------
        xgrids : nd.array
            concatenation of the subgrids
        
        Returns
        -------
        xgrid_list : list
            list containing the different grids
        """
        xgrid_list = []
        imin = 0
        for i in range(1, len(xgrids)):
            if xgrids[i-1] > xgrids[i] :
                xgrid_list.append(xgrids[imin:i])
                imin = i
        xgrid_list.append(xgrids[imin:])
        return xgrid_list
    
    def F2LO(self, x, Q):
        r"""
        Compute the LO DIS structure function F2.

        Parameters
        ----------
        x : float
            Bjorken's variable
        Q : float
            DIS hard scale
        
        Returns
        -------
        F2_LO : float
            Structure function F2 at LO
        """
        # at LO we use ZM-VFS
        if Q < self.theory["Qmc"] :
            nf = 3
        elif Q < self.theory["Qmb"] :
            nf = 4
        elif Q < self.theory["Qmt"] :
            nf = 5
        else :
            nf = 6
        res = 0
        for i in range(1, nf+1):
            res += self.eq2[i-1] * (self.qcd_pdfs.xfxQ(x, Q)[i] + self.qcd_pdfs.xfxQ(x, Q)[-i])
        return res

    def alpha_em(self, q):
        r"""
        Compute the value of alpha_em.

        Parameters
        ----------
        q: float
            value in which the coupling is computed
        
        Returns
        -------
        alpha_em: float
            electromagnetic coupling
        """
        if q < self.theory["Qmc"] :
            nf = 3
        elif q < self.theory["Qmb"] :
            nf = 4
        elif q < self.theory["Qmt"] :
            nf = 5
        else :
            nf = 6
        return self.a_em_nlo(
            q,
            self.a_thresh[nf],
            self.thresh[nf],
            nf
        ) * (4 * np.pi)
    
    def a_em_nlo(self, q, a_ref, qref, nf):
        nl = 3
        nc = 3
        nu = nf // 2
        nd = nf - nu
        beta0 = ( -4.0 / 3 * (nl + nc * (nu * self.eu2 + nd * self.ed2)) )
        beta1 = -4.0 * ( nl + nc * (nu * self.eu2**2 + nd * self.ed2**2) )
        lmu = np.log(q / qref)
        den = 1.0 + beta0 * a_ref * lmu
        a_LO = a_ref / den
        as_NLO = a_LO * (1 - beta1 / beta0 * a_LO * np.log(den))
        return as_NLO
    
    def set_thresholds_a_em(self):
        a_ref = self.alpha_em_ref / (4 * np.pi)
        self.a_em_mt = self.a_em_nlo(self.theory["Qmt"], a_ref, self.qref, 5)
        self.a_em_mb = self.a_em_nlo(self.theory["Qmb"], a_ref, self.qref, 5)
        self.a_em_mc = self.a_em_nlo(self.theory["Qmc"], self.a_em_mb, self.theory["Qmb"], 4)

        self.thresh = {3: self.theory["Qmc"], 4: self.theory["Qmb"], 5: self.qref, 6:self.theory["Qmt"]}
        self.a_thresh = {3: self.a_em_mc, 4:self.a_em_mb, 5:self.alpha_em_ref/(4*np.pi), 6:self.a_em_mt}

    def compute_photon_array(self, xgrids):
        r"""
        Compute the photon PDF for every point in the grid xgrid.

        Parameters
        ----------
        xgrids: numpy.array
            grid of the x points
        
        Returns
        -------
        compute_photon_array: numpy.array
            photon PDF at the scale 1 GeV
        """
        xgrid_list = self.exctract_grids(xgrids)
        
        photon_list = []
        for xgrid in xgrid_list :
            photon_100GeV = np.zeros(len(xgrid))
            for i, x in enumerate(xgrid):
                print("computing grid point", i+1, "/", len(xgrids))
                photon_100GeV[i] = self.lux.EvaluatePhoton(x, self.q_in2).total / x

            eko=load_tar(self.fiatlux_runcard['path_to_eko'])
            xgrid_reshape(eko, targetgrid = XGrid(xgrid), inputgrid = XGrid(xgrid))
            
            pdfs = np.zeros((len(eko.rotations.inputpids), len(xgrid)))
            for j, pid in enumerate(eko.rotations.inputpids):
                if pid == 22 :
                    pdfs[j] = photon_100GeV
                    ph_id = j
                if not self.qcd_pdfs.hasFlavor(pid):
                    continue
                pdfs[j] = np.array(
                    [
                        self.qcd_pdfs.xfxQ2(pid, x, self.q_in2) / x
                        for x in xgrid
                    ]
                )
            
            for q2, elem in eko.items():
                pdf_final = np.einsum("ajbk,bk", elem.operator, pdfs)
                # error_final = np.einsum("ajbk,bk", elem.error, pdfs)

            photon_Q0 = pdf_final[ph_id]
            # we want x * gamma(x)
            photon_list.append( xgrid * photon_Q0 )
       
        return np.concatenate(photon_list)
    
    def produce_interpolator(self):
        # TODO : pass the grid in a more clever way
        self.xgrid = np.array([1.00000000000000e-09, 1.29708482343957e-09, 1.68242903474257e-09, 2.18225315420583e-09, 2.83056741739819e-09, 3.67148597892941e-09, 4.76222862935315e-09, 6.17701427376180e-09, 8.01211109898438e-09, 1.03923870607245e-08, 1.34798064073805e-08, 1.74844503691778e-08, 2.26788118881103e-08, 2.94163370300835e-08, 3.81554746595878e-08, 4.94908707232129e-08, 6.41938295708371e-08, 8.32647951986859e-08, 1.08001422993829e-07, 1.40086873081130e-07, 1.81704331793772e-07, 2.35685551545377e-07, 3.05703512595323e-07, 3.96522309841747e-07, 5.14321257236570e-07, 6.67115245136676e-07, 8.65299922973143e-07, 1.12235875241487e-06, 1.45577995547683e-06, 1.88824560514613e-06, 2.44917352454946e-06, 3.17671650028717e-06, 4.12035415232797e-06, 5.34425265752090e-06, 6.93161897806315e-06, 8.99034258238145e-06, 1.16603030112258e-05, 1.51228312288769e-05, 1.96129529349212e-05, 2.54352207134502e-05, 3.29841683435992e-05, 4.27707053972016e-05, 5.54561248105849e-05, 7.18958313632514e-05, 9.31954227979614e-05, 1.20782367731330e-04, 1.56497209466554e-04, 2.02708936328495e-04, 2.62459799331951e-04, 3.39645244168985e-04, 4.39234443000422e-04, 5.67535660104533e-04, 7.32507615725537e-04, 9.44112105452451e-04, 1.21469317686978e-03, 1.55935306118224e-03, 1.99627451141338e-03, 2.54691493736552e-03, 3.23597510213126e-03, 4.09103436509565e-03, 5.14175977083962e-03, 6.41865096062317e-03, 7.95137940306351e-03, 9.76689999624100e-03, 1.18876139251364e-02, 1.43298947643919e-02, 1.71032279460271e-02, 2.02100733925079e-02, 2.36463971369542e-02, 2.74026915728357e-02, 3.14652506132444e-02, 3.58174829282429e-02, 4.04411060163317e-02, 4.53171343973807e-02, 5.04266347950069e-02, 5.57512610084339e-02, 6.12736019390519e-02, 6.69773829498255e-02, 7.28475589986517e-02, 7.88703322292727e-02, 8.50331197801452e-02, 9.13244910278679e-02, 9.77340879783772e-02, 1.04252538208639e-01, 1.10871366547237e-01, 1.17582909372878e-01, 1.24380233801599e-01, 1.31257062945031e-01, 1.38207707707289e-01, 1.45227005135651e-01, 1.52310263065985e-01, 1.59453210652156e-01, 1.66651954293987e-01, 1.73902938455578e-01, 1.81202910873333e-01, 1.88548891679097e-01, 1.95938145999193e-01, 2.03368159629765e-01, 2.10836617429103e-01, 2.18341384106561e-01, 2.25880487124065e-01, 2.33452101459503e-01, 2.41054536011681e-01, 2.48686221452762e-01, 2.56345699358723e-01, 2.64031612468684e-01, 2.71742695942783e-01, 2.79477769504149e-01, 2.87235730364833e-01, 2.95015546847664e-01, 3.02816252626866e-01, 3.10636941519503e-01, 3.18476762768082e-01, 3.26334916761672e-01, 3.34210651149156e-01, 3.42103257303627e-01, 3.50012067101685e-01, 3.57936449985571e-01, 3.65875810279643e-01, 3.73829584735962e-01, 3.81797240286494e-01, 3.89778271981947e-01, 3.97772201099286e-01, 4.05778573402340e-01, 4.13796957540671e-01, 4.21826943574548e-01, 4.29868141614175e-01, 4.37920180563205e-01, 4.45982706956990e-01, 4.54055383887562e-01, 4.62137890007651e-01, 4.70229918607142e-01, 4.78331176755675e-01, 4.86441384506059e-01, 4.94560274153348e-01, 5.02687589545177e-01, 5.10823085439086e-01, 5.18966526903235e-01, 5.27117688756998e-01, 5.35276355048428e-01, 5.43442318565661e-01, 5.51615380379768e-01, 5.59795349416641e-01, 5.67982042055800e-01, 5.76175281754088e-01, 5.84374898692498e-01, 5.92580729444440e-01, 6.00792616663950e-01, 6.09010408792398e-01, 6.17233959782450e-01, 6.25463128838069e-01, 6.33697780169485e-01, 6.41937782762089e-01, 6.50183010158361e-01, 6.58433340251944e-01, 6.66688655093089e-01, 6.74948840704708e-01, 6.83213786908386e-01, 6.91483387159697e-01, 6.99757538392251e-01, 7.08036140869916e-01, 7.16319098046733e-01, 7.24606316434025e-01, 7.32897705474271e-01, 7.41193177421404e-01, 7.49492647227008e-01, 7.57796032432224e-01, 7.66103253064927e-01, 7.74414231541921e-01, 7.82728892575836e-01, 7.91047163086478e-01, 7.99368972116378e-01, 8.07694250750291e-01, 8.16022932038457e-01, 8.24354950923382e-01, 8.32690244169987e-01, 8.41028750298844e-01, 8.49370409522600e-01, 8.57715163684985e-01, 8.66062956202683e-01, 8.74413732009721e-01, 8.82767437504206e-01, 8.91124020497459e-01, 8.99483430165226e-01, 9.07845617001021e-01, 9.16210532771399e-01, 9.24578130473112e-01, 9.32948364292029e-01, 9.41321189563734e-01, 9.49696562735755e-01, 9.58074441331298e-01, 9.66454783914439e-01, 9.74837550056705e-01, 9.83222700304978e-01, 9.91610196150662e-01, 1.00000000000000e+00])
        self.photon_array = self.compute_photon_array(self.xgrid)
        self.interpolator = interp1d(self.xgrid, self.photon_array, fill_value=0.)
    
    def compute(self, xgrid):
        return self.interpolator(xgrid[0,:,0])[np.newaxis,:,np.newaxis]
    
    def integrate(self):
        return trapezoid(self.photon_array, self.xgrid)