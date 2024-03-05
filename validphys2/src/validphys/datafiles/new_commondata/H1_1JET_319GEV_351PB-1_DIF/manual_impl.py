from math import sqrt
from validphys.commondata_utils import cormat_to_covmat as ctc
from validphys.commondata_utils import covmat_to_artunc as cta

jet_old_impl_list = [['1', 'DIS_1JET', '1.750000000000e+02', '9.000000000000e+00', '3.190000000000e+02', '7.042365878823e+01', '1.901438787282e+00', '7.042365878823e-01', '1.000000000000e+00', '7.130250486484e-01', '1.010961455291e+00', '6.718827732504e-01', '9.531044964111e-01', '2.517144109385e-01', '3.572500464504e-01', '2.515885537330e-01', '3.572500464504e-01', '3.521182939412e-01', '5.000000000000e-01', '4.225419527294e-01', '6.000000000000e-01', '2.042286104859e+00', '2.900000000000e+00'], ['2', 'DIS_1JET', '1.750000000000e+02', '1.450000000000e+01', '3.190000000000e+02', '3.095350776162e+01', '1.269093818226e+00', '8.666982173254e-01', '2.800000000000e+00', '7.598162606841e-01', '2.452246318915e+00', '1.718173641914e-01', '5.542497004702e-01', '1.910967863178e-01', '6.170584587557e-01', '8.045980207445e-02', '2.599375899303e-01', '1.547675388081e-01', '5.000000000000e-01', '1.857210465697e-01', '6.000000000000e-01', '8.976517250870e-01', '2.900000000000e+00'], ['3', 'DIS_1JET', '1.750000000000e+02', '2.400000000000e+01', '3.190000000000e+02', '8.082109035000e+00', '5.172549782400e-01', '2.828738162250e-01', '3.500000000000e+00', '2.743800000000e-01', '3.400000000000e+00', '1.976738222426e-02', '2.447042700083e-01', '3.679736009134e-02', '4.552940319412e-01', '8.082109035000e-03', '1.000000000000e-01', '4.041054517500e-02', '5.000000000000e-01', '4.849265421000e-02', '6.000000000000e-01', '2.343811620150e-01', '2.900000000000e+00'], ['4', 'DIS_1JET', '1.750000000000e+02', '4.000000000000e+01', '3.190000000000e+02', '9.125014074304e-01', '1.396127153368e-01', '1.067626646694e-01', '1.170000000000e+01', '4.688994472166e-02', '5.118073262173e+00', '1.519286117216e-03', '1.657483653351e-01', '4.299338659215e-03', '4.704529347867e-01', '1.991738317891e-03', '2.182723557106e-01', '4.562507037152e-03', '5.000000000000e-01', '5.475008444582e-03', '6.000000000000e-01', '2.646254081548e-02', '2.900000000000e+00'], ['5', 'DIS_1JET', '2.350000000000e+02', '9.000000000000e+00', '3.190000000000e+02', '5.493706846573e+01', '1.648112053972e+00', '-3.296224107944e-01', '-6.000000000000e-01', '5.220401134013e-01', '9.531044964111e-01', '6.074575198510e-01', '1.107945704936e+00', '4.273370774492e-01', '7.782554801857e-01', '1.960665379920e-01', '3.568929749397e-01', '2.746853423286e-01', '5.000000000000e-01', '3.296224107944e-01', '6.000000000000e-01', '1.593174985506e+00', '2.900000000000e+00'], ['6', 'DIS_1JET', '2.350000000000e+02', '1.450000000000e+01', '3.190000000000e+02', '2.680000000000e+01', '1.098800000000e+00', '9.112000000000e-01', '3.400000000000e+00', '6.432000000000e-01', '2.400000000000e+00', '1.072000000000e-01', '4.000000000000e-01', '1.608000000000e-01', '6.000000000000e-01', '8.040000000000e-02', '3.000000000000e-01', '1.340000000000e-01', '5.000000000000e-01', '1.608000000000e-01', '6.000000000000e-01', '7.772000000000e-01', '2.900000000000e+00'], ['7', 'DIS_1JET', '2.350000000000e+02', '2.400000000000e+01', '3.190000000000e+02', '7.013496240129e+00', '4.628907518485e-01', '3.366478195262e-01', '4.800000000000e+00', '2.492988998672e-01', '3.551005871609e+00', '1.404103000000e-02', '2.000000000000e-01', '3.893063895065e-02', '5.548042274342e-01', '2.505571857565e-02', '3.572500464504e-01', '3.506748120064e-02', '5.000000000000e-01', '4.208097744077e-02', '6.000000000000e-01', '2.033913909637e-01', '2.900000000000e+00'], ['8', 'DIS_1JET', '2.350000000000e+02', '4.000000000000e+01', '3.190000000000e+02', '8.549775241245e-01', '1.299565836669e-01', '3.932896610973e-02', '4.600000000000e+00', '4.505743015308e-02', '5.264739441654e+00', '1.865246959223e-03', '2.182723557106e-01', '7.400622244443e-04', '8.655926074807e-02', '2.564932572373e-03', '3.000000000000e-01', '4.274887620623e-03', '5.000000000000e-01', '5.129865144747e-03', '6.000000000000e-01', '2.479434819961e-02', '2.900000000000e+00'], ['9', 'DIS_1JET', '3.450000000000e+02', '9.000000000000e+00', '3.190000000000e+02', '5.209563915000e+01', '1.562869174500e+00', '7.814345872500e-01', '1.500000000000e+00', '4.972717868530e-01', '9.531044964111e-01', '5.217390000000e-01', '1.000000000000e+00', '4.570802892413e-01', '8.773868536773e-01', '1.562869174500e-01', '3.000000000000e-01', '2.604781957500e-01', '5.000000000000e-01', '3.125738349000e-01', '6.000000000000e-01', '1.510773535350e+00', '2.900000000000e+00'], ['10', 'DIS_1JET', '3.450000000000e+02', '1.450000000000e+01', '3.190000000000e+02', '2.785563475695e+01', '1.114225390278e+00', '8.635246774655e-01', '3.100000000000e+00', '6.258088126577e-01', '2.249985843976e+00', '1.112556000000e-01', '4.000000000000e-01', '2.259611917827e-01', '8.115922482154e-01', '7.233489456689e-02', '2.596777822442e-01', '1.114225390278e-01', '4.000000000000e-01', '1.671338085417e-01', '6.000000000000e-01', '8.078134079515e-01', '2.900000000000e+00'], ['11', 'DIS_1JET', '3.450000000000e+02', '2.400000000000e+01', '3.190000000000e+02', '6.962069709237e+00', '4.734207402281e-01', '1.322793244755e-01', '1.900000000000e+00', '2.518340918144e-01', '3.606383090020e+00', '1.158001203865e-02', '1.657483653351e-01', '5.928243109147e-02', '8.502285946131e-01', '1.811516043400e-02', '2.601979180124e-01', '2.784827883695e-02', '4.000000000000e-01', '4.177241825542e-02', '6.000000000000e-01', '2.019000215679e-01', '2.900000000000e+00'], ['12', 'DIS_1JET', '3.450000000000e+02', '4.000000000000e+01', '3.190000000000e+02', '8.702993693220e-01', '1.314152047676e-01', '-2.610898107966e-02', '-3.000000000000e+00', '4.826471687216e-02', '5.562396168725e+00', '1.502894423550e-03', '1.733784592161e-01', '5.667628733710e-03', '6.522043307043e-01', '2.849193515760e-03', '3.273808549327e-01', '3.481197477288e-03', '4.000000000000e-01', '5.221796215932e-03', '6.000000000000e-01', '2.523868171034e-02', '2.900000000000e+00'], ['13', 'DIS_1JET', '5.500000000000e+02', '9.000000000000e+00', '3.190000000000e+02', '4.877557560000e+01', '1.560818419200e+00', '7.316336340000e-01', '1.500000000000e+00', '6.381428053344e-01', '1.308978661724e+00', '3.412584000000e-01', '7.000000000000e-01', '5.616976088752e-01', '1.151596064148e+00', '9.755115120000e-02', '2.000000000000e-01', '1.951023024000e-01', '4.000000000000e-01', '2.926534536000e-01', '6.000000000000e-01', '1.414491692400e+00', '2.900000000000e+00'], ['14', 'DIS_1JET', '5.500000000000e+02', '1.450000000000e+01', '3.190000000000e+02', '2.690000000000e+01', '1.102900000000e+00', '3.228000000000e-01', '1.200000000000e+00', '5.380000000000e-01', '2.000000000000e+00', '1.076000000000e-01', '4.000000000000e-01', '1.883000000000e-01', '7.000000000000e-01', '2.690000000000e-02', '1.000000000000e-01', '1.076000000000e-01', '4.000000000000e-01', '1.614000000000e-01', '6.000000000000e-01', '7.801000000000e-01', '2.900000000000e+00'], ['15', 'DIS_1JET', '5.500000000000e+02', '2.400000000000e+01', '3.190000000000e+02', '7.949992050000e+00', '4.849495150500e-01', '2.782497217500e-01', '3.500000000000e+00', '2.943647864470e-01', '3.699002713601e+00', '2.639353425041e-02', '3.319944735090e-01', '6.359993640000e-02', '8.000000000000e-01', '7.949992050000e-03', '1.000000000000e-01', '2.384997615000e-02', '3.000000000000e-01', '4.769995230000e-02', '6.000000000000e-01', '2.305497694500e-01', '2.900000000000e+00'], ['16', 'DIS_1JET', '5.500000000000e+02', '4.000000000000e+01', '3.190000000000e+02', '8.561421438570e-01', '1.412634537364e-01', '-7.619665080327e-02', '-8.900000000000e+00', '4.800730113222e-02', '5.596189240424e+00', '1.213193003977e-03', '1.415629191565e-01', '1.211979810973e-03', '1.415629191565e-01', '8.561421438570e-04', '1.000000000000e-01', '1.712284287714e-03', '2.000000000000e-01', '5.136852863142e-03', '6.000000000000e-01', '2.482812217185e-02', '2.900000000000e+00'], ['17', 'DIS_1JET', '2.850000000000e+03', '9.000000000000e+00', '3.190000000000e+02', '4.329996751417e+01', '1.515498862996e+00', '9.525992853119e-01', '2.200000000000e+00', '4.802202307275e-01', '1.110163814455e+00', '1.970436461015e-01', '4.552940319412e-01', '1.971421679245e-01', '4.552940319412e-01', '2.164998375709e-01', '5.000000000000e-01', '4.762996426559e-01', '1.100000000000e+00', '2.597998050850e-01', '6.000000000000e-01', '1.255699057911e+00', '2.900000000000e+00'], ['18', 'DIS_1JET', '2.850000000000e+03', '1.450000000000e+01', '3.190000000000e+02', '2.852850712500e+01', '1.141140285000e+00', '3.993990997500e-01', '1.400000000000e+00', '4.422094385017e-01', '1.550836646595e+00', '2.851425000000e-02', '1.000000000000e-01', '1.581191652889e-01', '5.542497004702e-01', '1.711710427500e-01', '6.000000000000e-01', '3.138135783750e-01', '1.100000000000e+00', '1.711710427500e-01', '6.000000000000e-01', '8.273267066250e-01', '2.900000000000e+00'], ['19', 'DIS_1JET', '2.850000000000e+03', '2.400000000000e+01', '3.190000000000e+02', '1.069999732500e+01', '5.242998689250e-01', '2.888999277750e-01', '2.700000000000e+00', '2.943472566544e-01', '2.752285083237e+00', '1.069465000000e-02', '1.000000000000e-01', '5.930470312414e-02', '5.542497004702e-01', '4.279998930000e-02', '4.000000000000e-01', '1.176999705750e-01', '1.100000000000e+00', '6.419998395000e-02', '6.000000000000e-01', '3.102999224250e-01', '2.900000000000e+00'], ['20', 'DIS_1JET', '2.850000000000e+03', '4.000000000000e+01', '3.190000000000e+02', '2.044081530000e+00', '1.737469300500e-01', '4.292571213000e-02', '2.100000000000e+00', '9.495865837300e-02', '4.647864398158e+00', '1.769341861456e-03', '8.655926074807e-02', '6.132244590000e-03', '3.000000000000e-01', '4.088163060000e-03', '2.000000000000e-01', '2.044081530000e-02', '1.000000000000e+00', '1.226448918000e-02', '6.000000000000e-01', '5.927836437000e-02', '2.900000000000e+00'], ['21', 'DIS_1JET', '1.000000000000e+04', '9.000000000000e+00', '3.190000000000e+02', '2.571395501979e+00', '3.779951387908e-01', '-7.714186505936e-02', '-3.000000000000e+00', '2.217633874200e-02', '8.533627868550e-01', '1.102535035362e-02', '4.246887574694e-01', '4.242064477684e-02', '1.652187526630e+00', '1.277337104494e-02', '4.967485956598e-01', '4.885651453759e-02', '1.900000000000e+00', '1.542837301187e-02', '6.000000000000e-01', '7.457046955738e-02', '2.900000000000e+00'], ['22', 'DIS_1JET', '1.000000000000e+04', '1.450000000000e+01', '3.190000000000e+02', '1.760953607685e+00', '2.887963916604e-01', '1.937048968454e-02', '1.100000000000e+00', '2.485217093133e-02', '1.425434816076e+00', '1.509897970990e-03', '8.655926074807e-02', '1.934579665249e-02', '1.101344240954e+00', '1.299737337559e-02', '7.380872113191e-01', '3.169716493834e-02', '1.800000000000e+00', '1.056572164611e-02', '6.000000000000e-01', '5.106765462288e-02', '2.900000000000e+00'], ['23', 'DIS_1JET', '1.000000000000e+04', '2.400000000000e+01', '3.190000000000e+02', '6.709991612502e-01', '1.449358188300e-01', '-8.655889180127e-02', '-1.290000000000e+01', '1.412291623568e-02', '2.102653864121e+00', '1.745052446956e-03', '2.599375899303e-01', '1.162786613822e-03', '1.733784592161e-01', '3.719010841387e-03', '5.542497004702e-01', '1.207798490250e-02', '1.800000000000e+00', '4.025994967501e-03', '6.000000000000e-01', '1.945897567625e-02', '2.900000000000e+00'], ['24', 'DIS_1JET', '1.000000000000e+04', '4.000000000000e+01', '3.190000000000e+02', '3.085353405933e-01', '6.078146209687e-02', '-6.016439141569e-02', '-1.950000000000e+01', '8.809210109312e-03', '2.849452331864e+00', '2.677356506943e-04', '8.655926074807e-02', '2.272948236221e-03', '7.370580971263e-01', '2.670659099641e-04', '8.655926074807e-02', '5.553636130679e-03', '1.800000000000e+00', '1.851212043560e-03', '6.000000000000e-01', '8.947524877205e-03', '2.900000000000e+00']]
dijet_old_impl_list = [['1', 'DIS_2JET', '1.750000000000e+02', '9.000000000000e+00', '3.190000000000e+02', '2.332986433245e+01', '8.398751159682e-01', '4.899271509815e-01', '2.100000000000e+00', '5.731805998113e-02', '2.451941684468e-01', '3.038958000000e-01', '1.300000000000e+00', '9.567285880348e-02', '4.098824622871e-01', '8.334595116449e-02', '3.572500464504e-01', '1.166493216623e-01', '5.000000000000e-01', '1.399791859947e-01', '6.000000000000e-01', '6.765660656411e-01', '2.900000000000e+00'], ['2', 'DIS_2JET', '1.750000000000e+02', '1.450000000000e+01', '3.190000000000e+02', '1.359998980340e+01', '7.887994085972e-01', '4.759996431190e-01', '3.500000000000e+00', '2.517837167094e-01', '1.852276996656e+00', '3.531616955617e-02', '2.599375899303e-01', '2.717280680000e-02', '2.000000000000e-01', '4.506100232821e-02', '3.313311478877e-01', '6.799994901700e-02', '5.000000000000e-01', '8.159993882040e-02', '6.000000000000e-01', '3.943997042986e-01', '2.900000000000e+00'], ['3', 'DIS_2JET', '1.750000000000e+02', '2.400000000000e+01', '3.190000000000e+02', '3.569995537501e+00', '2.391897010126e-01', '1.427998215000e-01', '4.000000000000e+00', '1.410375931268e-01', '3.948658531429e+00', '6.186513093712e-03', '1.730320487082e-01', '1.185811694750e-02', '3.319944735090e-01', '5.923129415274e-03', '1.659141966161e-01', '1.784997768750e-02', '5.000000000000e-01', '2.141997322501e-02', '6.000000000000e-01', '1.035298705875e-01', '2.900000000000e+00'], ['4', 'DIS_2JET', '1.750000000000e+02', '4.000000000000e+01', '3.190000000000e+02', '4.187346492079e-01', '6.867248247009e-02', '3.266130263821e-02', '7.800000000000e+00', '2.168091095872e-02', '5.149248535500e+00', '5.954546204372e-04', '1.412800761611e-01', '3.009905338278e-03', '7.177315003561e-01', '9.139819830025e-04', '2.182723557106e-01', '2.093673246039e-03', '5.000000000000e-01', '2.512407895247e-03', '6.000000000000e-01', '1.214330482703e-02', '2.900000000000e+00'], ['5', 'DIS_2JET', '2.350000000000e+02', '9.000000000000e+00', '3.190000000000e+02', '1.815435885215e+01', '7.443287129383e-01', '3.630871770431e-01', '2.000000000000e+00', '1.567505980850e-02', '8.655926074807e-02', '2.368065567406e-01', '1.306363319742e+00', '9.419148141445e-02', '5.190961461245e-01', '8.265571239106e-02', '4.552940319412e-01', '9.077179426077e-02', '5.000000000000e-01', '1.089261531129e-01', '6.000000000000e-01', '5.264764067125e-01', '2.900000000000e+00'], ['6', 'DIS_2JET', '2.350000000000e+02', '1.450000000000e+01', '3.190000000000e+02', '1.238138760000e+01', '6.933577056000e-01', '2.723905272000e-01', '2.200000000000e+00', '2.750453053590e-01', '2.222552406094e+00', '4.950080000000e-02', '4.000000000000e-01', '8.091336930916e-02', '6.535080874874e-01', '3.714416280000e-02', '3.000000000000e-01', '6.190693800000e-02', '5.000000000000e-01', '7.428832560000e-02', '6.000000000000e-01', '3.590602404000e-01', '2.900000000000e+00'], ['7', 'DIS_2JET', '2.350000000000e+02', '2.400000000000e+01', '3.190000000000e+02', '2.951471313606e+00', '2.184088772069e-01', '1.180588525442e-01', '4.000000000000e+00', '1.049118052223e-01', '3.551005871609e+00', '4.899359598123e-03', '1.659141966161e-01', '2.952947787500e-03', '1.000000000000e-01', '7.671983400072e-03', '2.599375899303e-01', '1.475735656803e-02', '5.000000000000e-01', '1.770882788164e-02', '6.000000000000e-01', '8.559266809458e-02', '2.900000000000e+00'], ['8', 'DIS_2JET', '2.350000000000e+02', '4.000000000000e+01', '3.190000000000e+02', '3.848578386965e-01', '6.965926880406e-02', '4.772237199836e-02', '1.240000000000e+01', '2.070126341555e-02', '5.368181183352e+00', '8.404589203493e-04', '2.182723557106e-01', '3.334635636703e-04', '8.655926074807e-02', '1.277706755339e-03', '3.319944735090e-01', '1.924289193482e-03', '5.000000000000e-01', '2.309147032179e-03', '6.000000000000e-01', '1.116087732220e-02', '2.900000000000e+00'], ['9', 'DIS_2JET', '3.450000000000e+02', '9.000000000000e+00', '3.190000000000e+02', '1.829085000000e+01', '7.133431500000e-01', '1.829085000000e-01', '1.000000000000e+00', '0.000000000000e+00', '0.000000000000e+00', '2.013000000000e-01', '1.100000000000e+00', '9.150000000000e-02', '5.000000000000e-01', '4.754479466777e-02', '2.599375899303e-01', '7.316340000000e-02', '4.000000000000e-01', '1.097451000000e-01', '6.000000000000e-01', '5.304346500000e-01', '2.900000000000e+00'], ['10', 'DIS_2JET', '3.450000000000e+02', '1.450000000000e+01', '3.190000000000e+02', '1.129435000000e+01', '6.889553500000e-01', '4.178909500000e-01', '3.700000000000e+00', '2.486000000000e-01', '2.200000000000e+00', '3.390000000000e-02', '3.000000000000e-01', '6.266153126121e-02', '5.548042274342e-01', '3.388305000000e-02', '3.000000000000e-01', '4.517740000000e-02', '4.000000000000e-01', '6.776610000000e-02', '6.000000000000e-01', '3.275361500000e-01', '2.900000000000e+00'], ['11', 'DIS_2JET', '3.450000000000e+02', '2.400000000000e+01', '3.190000000000e+02', '3.784819941450e+00', '2.270891964870e-01', '4.541783929740e-02', '1.200000000000e+00', '1.313475922886e-01', '3.461708148764e+00', '3.794300000000e-03', '1.000000000000e-01', '1.244044449638e-02', '3.283644729245e-01', '5.357901593933e-03', '1.415629191565e-01', '1.513927976580e-02', '4.000000000000e-01', '2.270891964870e-02', '6.000000000000e-01', '1.097597783020e-01', '2.900000000000e+00'], ['12', 'DIS_2JET', '3.450000000000e+02', '4.000000000000e+01', '3.190000000000e+02', '3.388651500430e-01', '6.946735575881e-02', '-2.372056050301e-02', '-7.000000000000e+00', '1.977551253445e-02', '5.792136528160e+00', '8.870351800802e-04', '2.601979180124e-01', '2.045447220000e-03', '6.024096385542e-01', '9.603761342813e-04', '2.834095315377e-01', '1.355460600172e-03', '4.000000000000e-01', '2.033190900258e-03', '6.000000000000e-01', '9.827089351246e-03', '2.900000000000e+00'], ['13', 'DIS_2JET', '5.500000000000e+02', '9.000000000000e+00', '3.190000000000e+02', '1.673342087918e+01', '6.860702560462e-01', '1.171339461542e-01', '7.000000000000e-01', '2.361736649163e-02', '1.412800761611e-01', '1.425827699417e-01', '8.525098505363e-01', '5.972040358486e-02', '3.568929749397e-01', '3.346684175835e-02', '2.000000000000e-01', '6.693368351670e-02', '4.000000000000e-01', '1.004005252750e-01', '6.000000000000e-01', '4.852692054961e-01', '2.900000000000e+00'], ['14', 'DIS_2JET', '5.500000000000e+02', '1.450000000000e+01', '3.190000000000e+02', '1.078379730405e+01', '6.793792301552e-01', '3.774329056418e-01', '3.500000000000e+00', '2.225822095317e-01', '2.064042448225e+00', '3.850586794386e-02', '3.572500464504e-01', '5.976916425701e-02', '5.542497004702e-01', '1.078379730405e-02', '1.000000000000e-01', '4.313518921620e-02', '4.000000000000e-01', '6.470278382430e-02', '6.000000000000e-01', '3.127301218175e-01', '2.900000000000e+00'], ['15', 'DIS_2JET', '5.500000000000e+02', '2.400000000000e+01', '3.190000000000e+02', '3.651824087044e+00', '2.264130933967e-01', '8.034012991496e-02', '2.200000000000e+00', '1.186530736012e-01', '3.252395337426e+00', '3.648175000000e-03', '1.000000000000e-01', '1.302659032865e-02', '3.568929749397e-01', '6.052838729189e-03', '1.657483653351e-01', '1.095547226113e-02', '3.000000000000e-01', '2.191094452226e-02', '6.000000000000e-01', '1.059028985243e-01', '2.900000000000e+00'], ['16', 'DIS_2JET', '5.500000000000e+02', '4.000000000000e+01', '3.190000000000e+02', '3.780531631079e-01', '7.712284527401e-02', '-1.398796703499e-02', '-3.700000000000e+00', '2.142858760511e-02', '5.662474610362e+00', '3.277312925923e-04', '8.664586331010e-02', '1.134726852750e-03', '3.000000000000e-01', '3.275674269460e-04', '8.664586331010e-02', '7.561063262158e-04', '2.000000000000e-01', '2.268318978647e-03', '6.000000000000e-01', '1.096354173013e-02', '2.900000000000e+00'], ['17', 'DIS_2JET', '2.850000000000e+03', '9.000000000000e+00', '3.190000000000e+02', '1.492981862873e+01', '6.569120196639e-01', '1.492981862873e-01', '1.000000000000e+00', '6.787273016463e-02', '4.552940319412e-01', '8.266580922124e-02', '5.542497004702e-01', '1.065137174707e-01', '7.134294134408e-01', '5.971927451490e-02', '4.000000000000e-01', '1.791578235447e-01', '1.200000000000e+00', '8.957891177235e-02', '6.000000000000e-01', '4.329647402330e-01', '2.900000000000e+00'], ['18', 'DIS_2JET', '2.850000000000e+03', '1.450000000000e+01', '3.190000000000e+02', '1.320660000000e+01', '6.735366000000e-01', '2.773386000000e-01', '2.100000000000e+00', '1.980000000000e-01', '1.500000000000e+00', '2.188972361635e-02', '1.657483653351e-01', '3.961980000000e-02', '3.000000000000e-01', '6.603300000000e-02', '5.000000000000e-01', '1.452726000000e-01', '1.100000000000e+00', '7.923960000000e-02', '6.000000000000e-01', '3.829914000000e-01', '2.900000000000e+00'], ['19', 'DIS_2JET', '2.850000000000e+03', '2.400000000000e+01', '3.190000000000e+02', '4.769997615000e+00', '2.575798712100e-01', '2.384998807500e-01', '5.000000000000e+00', '1.216817557196e-01', '2.552256331931e+00', '7.906195049935e-03', '1.657483653351e-01', '1.239282042995e-02', '2.596777822442e-01', '1.704081869527e-02', '3.572500464504e-01', '5.246997376500e-02', '1.100000000000e+00', '2.861998569000e-02', '6.000000000000e-01', '1.383299308350e-01', '2.900000000000e+00'], ['20', 'DIS_2JET', '2.850000000000e+03', '4.000000000000e+01', '3.190000000000e+02', '9.574765845645e-01', '9.862008821014e-02', '1.914953169129e-02', '2.000000000000e+00', '4.404279943419e-02', '4.597575823778e+00', '1.659230195466e-03', '1.730320487082e-01', '3.144012940281e-03', '3.283644729245e-01', '9.574765845645e-04', '1.000000000000e-01', '9.574765845645e-03', '1.000000000000e+00', '5.744859507387e-03', '6.000000000000e-01', '2.776682095237e-02', '2.900000000000e+00'], ['21', 'DIS_2JET', '1.000000000000e+04', '9.000000000000e+00', '3.190000000000e+02', '7.304516141587e-01', '1.680038712565e-01', '-1.606993551149e-02', '-2.200000000000e+00', '4.766455994762e-03', '6.522043307043e-01', '3.013258361078e-03', '4.131368362342e-01', '9.247363761182e-03', '1.269776898659e+00', '4.246488757399e-03', '5.813511360763e-01', '1.533948389733e-02', '2.100000000000e+00', '4.382709684952e-03', '6.000000000000e-01', '2.118309681060e-02', '2.900000000000e+00'], ['22', 'DIS_2JET', '1.000000000000e+04', '1.450000000000e+01', '3.190000000000e+02', '8.706033123616e-01', '1.749912657847e-01', '8.270731467435e-02', '9.500000000000e+00', '1.947170447085e-02', '2.279271735273e+00', '1.416687987638e-03', '1.657483653351e-01', '1.753222436605e-02', '2.027898319008e+00', '1.279419312639e-02', '1.469577813997e+00', '1.567085962251e-02', '1.800000000000e+00', '5.223619874170e-03', '6.000000000000e-01', '2.524749605849e-02', '2.900000000000e+00'], ['23', 'DIS_2JET', '1.000000000000e+04', '2.400000000000e+01', '3.190000000000e+02', '3.432745801866e-01', '6.625199397602e-02', '-1.647717984896e-02', '-4.800000000000e+00', '7.582220782858e-03', '2.185670118954e+00', '1.150557039523e-03', '3.319944735090e-01', '3.213856823901e-03', '9.320219593463e-01', '3.391765881260e-03', '9.880620579059e-01', '6.522217023546e-03', '1.900000000000e+00', '2.059647481120e-03', '6.000000000000e-01', '9.954962825412e-03', '2.900000000000e+00'], ['24', 'DIS_2JET', '1.000000000000e+04', '4.000000000000e+01', '3.190000000000e+02', '1.496621703174e-01', '4.025912381538e-02', '-1.122466277381e-02', '-7.500000000000e+00', '3.816341965810e-03', '2.578104267278e+00', '2.563937489936e-04', '1.730320487082e-01', '2.067852779348e-03', '1.386516218276e+00', '1.218485308050e-03', '8.141571817822e-01', '2.693919065713e-03', '1.800000000000e+00', '8.979730219045e-04', '6.000000000000e-01', '4.340202939205e-03', '2.900000000000e+00']]

corMatArray = [
    100,-20,-11,-2,-14,2,1,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,35,1,-2,0,-5,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
-20,100,2,-1,4,-13,0,0,0,2,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-6,25,-1,-1,1,-3,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
-11,2,100,6,1,0,-13,-1,0,0,2,0,0,0,0,0,0,0,1,0,0,0,0,0,-1,-3,48,1,0,0,-6,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,
-2,-1,6,100,0,0,0,-14,0,0,0,2,0,0,0,0,0,0,0,1,0,0,0,1,0,1,-6,71,0,0,0,-10,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,
-14,4,1,0,100,-21,-10,-2,-11,2,1,0,-1,0,0,0,-1,0,0,0,0,0,0,0,-5,0,0,0,34,0,-1,0,-4,0,0,0,-1,0,0,0,-1,0,0,0,0,0,0,0,
2,-13,0,0,-21,100,2,-1,3,-10,0,0,0,0,0,0,0,-1,0,0,0,0,0,0,1,-4,0,0,-7,27,-1,0,1,-3,0,0,0,0,0,0,0,-1,0,0,0,0,0,0,
1,0,-13,0,-10,2,100,7,1,1,-12,0,0,0,0,0,0,0,-1,0,0,0,0,0,0,0,-7,0,-1,-3,49,-2,0,1,-6,0,0,0,0,0,0,0,-1,0,0,0,0,0,
0,0,-1,-14,-2,-1,7,100,0,0,0,-11,0,0,0,0,0,0,0,-1,0,0,0,0,0,0,1,-11,0,-1,-1,69,0,0,1,-7,0,0,0,0,0,0,0,-1,0,0,0,0,
1,0,0,0,-11,3,1,0,100,-23,-12,-2,-8,1,1,0,-1,0,0,0,0,0,0,0,1,0,0,0,-5,1,0,0,35,1,-1,0,-3,0,0,0,0,0,0,0,0,0,0,0,
0,2,0,0,2,-10,1,0,-23,100,0,-2,2,-8,0,0,0,0,0,0,0,0,0,0,0,1,0,0,1,-3,0,0,-6,25,0,-2,0,-2,0,0,0,-1,0,0,0,0,0,0,
0,0,2,0,1,0,-12,0,-12,0,100,5,1,1,-8,0,0,0,-1,0,0,0,0,0,0,0,1,0,0,1,-7,0,-1,-5,51,-1,0,0,-5,0,0,0,-1,0,0,0,-1,0,
0,0,0,2,0,0,0,-11,-2,-2,5,100,0,0,0,-8,0,0,0,0,0,0,0,0,0,0,0,2,0,0,0,-8,0,-1,-3,66,0,0,0,-6,0,0,0,-1,0,0,0,0,
0,0,0,0,-1,0,0,0,-8,2,1,0,100,-22,-11,-2,-4,1,0,0,0,0,0,0,0,0,0,0,-1,1,0,0,-3,1,0,0,35,0,-1,0,-2,0,0,0,0,0,0,0,
0,0,0,0,0,0,0,0,1,-8,1,0,-22,100,-1,-2,1,-4,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,-2,0,0,-6,25,-1,-1,0,-2,0,0,0,0,0,0,
0,0,0,0,0,0,0,0,1,0,-8,0,-11,-1,100,5,0,1,-4,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-4,0,-1,-2,48,-3,0,0,-3,0,0,0,0,0,
0,0,0,0,0,0,0,0,0,0,0,-8,-2,-2,5,100,0,0,0,-5,0,0,0,0,0,0,0,0,0,0,0,-1,0,0,0,-6,1,-1,-1,70,0,0,1,-4,0,0,0,1,
0,0,0,0,-1,0,0,0,-1,0,0,0,-4,1,0,0,100,-24,-12,-2,-1,0,0,0,1,0,0,0,-1,0,0,0,0,0,0,0,-2,0,0,0,32,1,-1,0,0,0,0,0,
0,0,0,0,0,-1,0,0,0,0,0,0,1,-4,1,0,-24,100,1,-2,0,-1,0,0,0,0,0,0,0,-1,0,0,0,0,1,0,0,-2,1,0,-7,24,-1,0,0,0,0,0,
0,0,1,0,0,0,-1,0,0,0,-1,0,0,0,-4,0,-12,1,100,3,0,0,-1,0,0,0,1,0,0,0,-1,0,0,0,-1,0,0,0,-3,1,-1,-4,50,-2,0,0,-1,0,
0,0,0,1,0,0,0,-1,0,0,0,0,0,0,0,16,-2,-2,3,100,0,0,0,-2,0,0,0,1,0,0,0,-1,0,0,1,-1,0,0,0,-4,0,0,-8,73,0,0,0,-2,
0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-1,0,0,0,100,-21,-15,-3,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,30,2,-2,-1,
0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-1,0,0,-21,100,-1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-8,21,0,-2,
0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-1,0,-15,-1,100,-2,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-1,0,-3,-3,44,-7,
0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-2,-3,0,-2,100,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-1,0,-2,-2,66,
35,-6,-1,0,-5,1,0,0,1,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,100,-44,11,3,-3,6,-2,0,11,-1,0,0,9,0,0,0,8,0,0,0,2,0,0,0,
1,25,-3,1,0,-4,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-44,100,-36,-9,7,-13,5,1,-1,2,-1,0,0,1,0,0,0,1,0,0,0,0,0,0,
-2,-1,48,-6,0,0,-7,1,0,0,1,0,0,0,0,0,0,0,1,0,0,0,0,0,11,-36,100,6,-1,4,-14,0,0,-1,2,0,0,0,1,0,0,0,1,0,0,0,1,0,
0,-1,1,71,0,0,0,-11,0,0,0,2,0,0,0,0,0,0,0,1,0,0,0,0,3,-9,6,100,0,1,0,-14,0,0,0,2,0,0,0,0,0,0,0,1,0,0,0,1,
-5,1,0,0,34,-7,-1,0,-5,1,0,0,-1,0,0,0,-1,0,0,0,0,0,0,0,-3,7,-1,0,100,-44,10,2,-4,6,-1,0,4,1,0,0,4,1,0,0,1,0,0,0,
0,-3,0,0,0,27,-3,-1,1,-3,1,0,1,0,0,0,0,-1,0,0,0,0,0,0,6,-13,4,1,-44,100,-34,-8,7,-11,4,1,1,-1,0,0,2,-1,0,0,0,0,0,0,
0,0,-6,0,-1,-1,49,-1,0,0,-7,0,0,0,0,0,0,0,-1,0,0,0,0,0,-2,5,-14,0,10,-34,100,2,-1,4,-12,0,0,0,0,0,0,0,-1,0,0,0,-1,0,
0,0,0,-10,0,0,-2,69,0,0,0,-8,0,0,0,-1,0,0,0,-1,0,0,0,0,0,1,0,-14,2,-8,2,100,0,1,1,-11,0,0,0,0,0,0,1,-2,0,1,1,0,
1,0,0,0,-4,1,0,0,35,-6,-1,0,-3,1,0,0,0,0,0,0,0,0,0,0,11,-1,0,0,-4,7,-1,0,100,-47,11,3,-3,5,-1,0,4,1,0,0,1,0,0,0,
0,1,0,0,0,-3,1,0,1,25,-5,-1,1,-2,0,0,0,0,0,0,0,0,0,0,-1,2,-1,0,6,-11,4,1,-47,100,-34,-10,5,-8,3,1,1,0,0,0,0,0,0,0,
0,0,1,0,0,0,-6,1,-1,0,51,-3,0,0,-4,0,0,1,-1,1,0,0,0,0,0,-1,2,0,-1,4,-12,1,11,-34,100,2,-1,3,-8,0,0,0,-1,1,0,0,-1,0,
0,0,0,1,0,0,0,-7,0,-2,-1,66,0,0,0,-6,0,0,0,-1,0,0,0,0,0,0,0,2,0,1,0,-11,3,-10,2,100,0,1,0,-9,0,0,0,-1,0,0,0,0,
0,0,0,0,-1,0,0,0,-3,0,0,0,35,-6,-1,1,-2,0,0,0,0,0,0,0,9,0,0,0,4,1,0,0,-3,5,-1,0,100,-45,11,3,-1,3,0,0,1,0,0,0,
0,0,0,0,0,0,0,0,0,-2,0,0,0,25,-2,-1,0,-2,0,0,0,0,0,0,0,1,0,0,1,-1,0,0,5,-8,3,1,-45,100,-36,-11,3,-4,2,1,0,0,0,0,
0,0,0,0,0,0,0,0,0,0,-5,0,-1,-1,48,-1,0,1,-3,0,0,0,0,0,0,0,1,0,0,0,0,0,-1,3,-8,0,11,-36,100,4,0,2,-5,0,0,0,0,0,
0,0,0,0,0,0,0,0,0,0,0,-6,0,-1,-3,70,0,0,1,-4,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,-9,3,-11,4,100,0,0,1,-6,0,0,1,1,
0,0,0,0,-1,0,0,0,0,0,0,0,-2,0,0,0,32,-7,-1,0,0,0,0,0,8,0,0,0,4,2,0,0,4,1,0,0,-1,3,0,0,100,-46,10,2,1,1,0,0,
0,0,0,0,0,-1,0,0,0,-1,0,0,0,-2,0,0,1,24,-4,0,0,0,0,0,0,1,0,0,1,-1,0,0,1,0,0,0,3,-4,2,0,-46,100,-35,-8,1,-1,0,0,
0,0,0,0,0,0,-1,0,0,0,-1,0,0,0,-3,1,-1,-1,50,-8,0,0,-1,0,0,0,1,0,0,0,-1,1,0,0,-1,0,0,2,-5,1,10,-35,100,-3,0,1,-1,-1,
0,0,0,0,0,0,0,-1,0,0,0,-1,0,0,0,-4,0,0,-2,73,0,0,0,-1,0,0,0,1,0,0,0,-2,0,0,1,-1,0,1,0,-6,2,-8,-3,100,0,0,1,2,
0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,30,-8,-3,0,2,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,1,0,0,100,-41,7,2,
0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,2,21,-3,-2,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,1,-1,1,0,-41,100,-36,-9,
0,0,0,0,0,0,0,0,0,0,-1,0,0,0,0,0,0,0,-1,0,-2,0,44,-2,0,0,1,0,0,0,-1,1,0,0,-1,0,0,0,0,1,0,0,-1,1,7,-36,100,-13,
0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,-2,-1,-2,-7,66,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,1,0,0,-1,2,2,-9,-13,100
]

def sys_breakdown(old_impl, is_jet):
    sys_breakdown = [[] for i in range(24)]
    for i in range(24):
        sys_breakdown[i].append(float(old_impl[i][7]))
        sys_breakdown[i].append(float(old_impl[i][9])/2)
        sys_breakdown[i].append(float(old_impl[i][9])/2)
        sys_breakdown[i].append(float(old_impl[i][11])/2)
        sys_breakdown[i].append(float(old_impl[i][11])/2)
        sys_breakdown[i].append(float(old_impl[i][13]))
        sys_breakdown[i].append(float(old_impl[i][15]))
        sys_breakdown[i].append(float(old_impl[i][17]))
        sys_breakdown[i].append(float(old_impl[i][5])*0.005) if is_jet else sys_breakdown[i].append(float(old_impl[i][19]))
        sys_breakdown[i].append(float(old_impl[i][21]))
    return sys_breakdown


def sym_data():
    jet_data = []
    dijet_data = []
    for i in range(24):
        jet_data.append(float(jet_old_impl_list[i][5]))
        dijet_data.append(float(dijet_old_impl_list[i][5]))
    return jet_data, dijet_data

def stat_lists():
    jet_stat = []
    dijet_stat = []
    for i in range(24):
        jet_stat.append(float(jet_old_impl_list[i][6]))
        dijet_stat.append(float(dijet_old_impl_list[i][6]))
    return jet_stat, dijet_stat

jet_data, dijet_data = sym_data()
jet_stat, dijet_stat = stat_lists()
jet_sys = sys_breakdown(jet_old_impl_list, True)
dijet_sys = sys_breakdown(dijet_old_impl_list, False)

covmat = ctc(jet_stat + dijet_stat, [a/100 for a in corMatArray])

artunc = cta(48, covmat, )

