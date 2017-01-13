/*
Inclusive total cross section for ttbar production @LHC CMS 8 TeV
There is a single point
 
LHC-CMS 13 TeV
---------------

emu events with b-tagged jets (L=2.2 1/fb)
[1603.02303]
sigma ttbar = 792 ± 8 (stat) ± 37 (syst) ± 21 (lumi) pb
 */

#include "CMSTTBARTOT13TEV.h"

void CMSTTBARTOT13TEVFilter::ReadData()
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
      fKin2[i] = Mt;             //top mass
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
      fSys[i][1].name = "CMSLUMI13";
      
      fData[i]*=(1.0 + dtmp*0.01); //Shift from asymmetric errors

    }  

  f1.close();

}
