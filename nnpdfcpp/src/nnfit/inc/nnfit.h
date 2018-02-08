// $Id: nnfit.h 1333 2013-11-20 16:46:42Z stefano.carrazza@mi.infn.it $
//
// NNPDF++ 2012-2015
//
// Authors: Nathan Hartland,  n.p.hartland@ed.ac.uk
//          Stefano Carrazza, stefano.carrazza@mi.infn.it

#include <string>
#include <vector>
#include <cstdlib>
#include <iostream>
#include <fstream>
#include <iomanip>
#include <cmath>
#include <sstream>
#include <sys/stat.h>

#include "nnpdfsettings.h"
#include <NNPDF/experiments.h>
#include <NNPDF/positivity.h>

class FitPDFSet;

// Fit status
enum fitStatus {FIT_INIT, FIT_END, FIT_ITER, FIT_ABRT};
fitStatus state(FIT_INIT);

void TrainValidSplit(const NNPDFSettings &settings, Experiment* const& exp, Experiment *&tr, Experiment *&val);

/**
 * @brief CreateResultsFolder
 * @param settings
 * @param replica
 */
void CreateResultsFolder(const NNPDFSettings &settings, const int replica)
{
  stringstream folder("");
  folder << settings.GetResultsDirectory() << "/nnfit";
  mkdir(folder.str().c_str(), 0777);
  folder << "/replica_" << replica;
  mkdir(folder.str().c_str(), 0777);
}


// Add chi^2 results to fit log
void LogChi2(NNPDFSettings const& settings,
             const FitPDFSet* pdf,
             vector<PositivitySet> const& pos,
             vector<Experiment*> const& train,
             vector<Experiment*> const& valid,
             vector<Experiment*> const& exp);

void LogPDF(NNPDFSettings const& settings,
            FitPDFSet* pdf,
            int replica);