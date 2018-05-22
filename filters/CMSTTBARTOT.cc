/*
Inclusive total cross section for ttbar production @LHC CMS
There are four points

LHC-CMS 5 TeV
---------------

emu events with b-tagged jets (L=27.4 1/pb)
[1711.03143]
sigma ttbar = 69.5 ± 6.1 (stat) +5.6 - 5.6 (syst) ± 1.6 (lumi) pb

LHC-CMS 7 TeV
---------------

emu events with b-tagged jets (L=5.0 1/fb)
[1603.02303]
sigma ttbar = 173.6 ± 2.1 (stat) +4.5 - 4.0 (syst) ± 3.8 (lumi) pb

LHC-CMS 8 TeV
---------------

emu events with b-tagged jets (L=19.7 1/fb)
[1603.02303]
sigma ttbar = 244.9 ± 1.4 (stat) +6.3 -5.5 (syst) ± 6.4 (lumi) pb

LHC-CMS 13 TeV
---------------

emu events with b-tagged jets (L=2.2 1/fb)
[1603.02303]
sigma ttbar = 792 ± 8 (stat) ± 37 (syst) ± 21 (lumi) pb

*/

#include "CMSTTBARTOT.h"

void CMSTTBARTOTFilter::ReadData()
{
  // Opening file
  fstream f1;
  stringstream datafile("");
  datafile << dataPath()
	   << "rawdata/" << fSetName << "/" << fSetName << ".data";
  f1.open(datafile.str().c_str(), ios::in);

  if (f1.fail())
    {
      cerr << "Error opening data file " << datafile.str() << endl;
      exit(-1);
    }

  //Starting filter
  for(int i=0; i<fNData;i++)
    {
      string line;
      int idum;
      double cme;
      double sys1, sys2;
      double stmp, dtmp;

      getline(f1,line);
      istringstream lstream(line);
      lstream >> idum >> cme;

      fKin1[i] = 0.;
      fKin2[i] = Mt*Mt;             //top mass
      fKin3[i] = cme*1000;       //sqrt(s)

      lstream >> fData[i];       //central value
      lstream >> fStat[i];       //statistical uncertainty
      lstream >> sys1 >> sys2;   //Asymmetric systematic uncertainty
      sys1 = sys1/fData[i]*100;
      sys2 = sys2/fData[i]*100;
      symmetriseErrors(sys1,sys2,&stmp,&dtmp);

      fSys[i][0].mult = stmp;    //Symmetric systematic uncertainty
      lstream >> fSys[i][1].add; //Luminosity uncertainty

      fSys[i][0].add = fSys[i][0].mult*fData[i]/100;
      fSys[i][0].type = MULT;
      fSys[i][0].name = "UNCORR";

      fSys[i][1].mult = fSys[i][1].add/fData[i]*100;
      fSys[i][1].type = MULT;
      fSys[i][1].name = "UNCORR";

      fData[i]*=(1.0 + dtmp*0.01); //Shift from asymmetric errors

    }

  f1.close();

}
