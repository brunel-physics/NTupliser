#Set up the pat environment
import FWCore.ParameterSet.Config as cms
process = cms.Process("customPAT")

from PhysicsTools.PatAlgos.tools.coreTools import *

#Setting up various environmental stuff that makes all of this jazz actually work.

###############################
####### Global Setup ##########
###############################

process.load('Configuration.Geometry.GeometryRecoDB_cff')
process.load('Configuration.StandardSequences.FrontierConditions_GlobalTag_condDBv2_cff')
process.load("Configuration.StandardSequences.MagneticField_cff")
process.load('PhysicsTools.PatAlgos.slimming.unpackedTracksAndVertices_cfi')

process.load("FWCore.MessageLogger.MessageLogger_cfi")
process.load("TrackingTools/TransientTrack/TransientTrackBuilder_cfi")

process.load('RecoBTag.Configuration.RecoBTag_cff')
process.load('RecoJets.Configuration.RecoJetAssociations_cff')
process.load('RecoJets.Configuration.RecoJetAssociations_cff')
process.load('TrackingTools.TransientTrack.TransientTrackBuilder_cfi')

process.load("FWCore.Framework.test.cmsExceptionsFatal_cff")
process.load("SimGeneral.HepPDTESSource.pythiapdt_cfi")
process.load("PhysicsTools.HepMCCandAlgos.genParticles_cfi")
process.load('Configuration.StandardSequences.Services_cff')

process.load("FWCore.MessageLogger.MessageLogger_cfi")
process.MessageLogger.destinations = ['cerr']
process.MessageLogger.statistics = []
process.MessageLogger.fwkJobReports = []
process.MessageLogger.categories=cms.untracked.vstring('FwkJob'
                                                       ,'FwkReport'
                                                       ,'FwkSummary'
                                                       )

process.MessageLogger.cerr.INFO = cms.untracked.PSet(limit = cms.untracked.int32(0))
process.MessageLogger.cerr.FwkReport.reportEvery = cms.untracked.int32(10000)
process.options = cms.untracked.PSet(
                     wantSummary = cms.untracked.bool(True)
                     )

from Configuration.AlCa.GlobalTag import GlobalTag
process.GlobalTag.globaltag = cms.string('76X_mcRun2_asymptotic_v12')

#There's a bit in here about some btau tags that the code looks for. I don't know if this is significant, however. I'm going to ignore it for now.

#Import jet reco things. Apparently this makes cmsRun crash.
process.load('RecoJets.Configuration.RecoPFJets_cff')

process.ak4JetTracksAssociatorAtVertexPF.jets = cms.InputTag("ak4PFJetsCHS")
process.ak4JetTracksAssociatorAtVertexPF.tracks = cms.InputTag("unpackedTracksAndVertices")
process.impactParameterTagInfos.primaryVertex = cms.InputTag("unpackedTracksAndVertices")
process.inclusiveSecondaryVertexFinderTagInfos.extSVCollection = cms.InputTag("unpackedTracksAndVertices","secondary","")


#Now do cool fast jet correction things!

process.ak4PFJets.doRhoFastjet = True

from PhysicsTools.SelectorUtils.pvSelector_cfi import pvSelector

## MET Filters __________________________________________________||
process.load('CommonTools.RecoAlgos.HBHENoiseFilterResultProducer_cfi')
process.load('PhysicsTools.PatAlgos.slimming.metFilterPaths_cff')
process.load('RecoMET.METFilters.eeBadScFilter_cfi')

process.goodVertices = cms.EDFilter(
      "VertexSelector",
        filter = cms.bool(False),
        src = cms.InputTag("offlineSlimmedPrimaryVertices"),
        cut = cms.string("!isFake && ndof > 4 && abs(z) <= 24 && position.rho < 2")
      )

process.primaryVertexFilter = cms.EDFilter("GoodVertexFilter",
                                           vertexCollection = cms.InputTag('offlineSlimmedPrimaryVertices'),
                                           minimumNDOF = cms.uint32(4) ,
                                           maxAbsZ = cms.double(24),
                                           maxd0 = cms.double(2)
                                           )

process.goodOfflinePrimaryVertices = cms.EDFilter(
    "PrimaryVertexObjectFilter",
    filterParams = cms.PSet( minNdof = cms.double( 4. ) ,
                             maxZ = cms.double( 24. ) ,
                             maxRho = cms.double( 2. ) ) ,
    filter = cms.bool( True) ,
    src = cms.InputTag( 'offlineSlimmedPrimaryVertices' ) )

process.eeBadScFilter.EERecHitSource = cms.InputTag('reducedEgamma', 'reducedEERecHits')


process.filtersSeq = cms.Sequence(
#    process.goodOfflinePrimaryVertices*
    process.primaryVertexFilter
    * process.HBHENoiseFilterResultProducer
    * process.HBHENoiseFilter
    * process.CSCTightHalo2015Filter
    * process.EcalDeadCellTriggerPrimitiveFilter
    * process.eeBadScFilter
    * process.goodVertices 
#    * process.trkPOGFilters
    )


###############################
###### Electron ID ############
###############################

from PhysicsTools.SelectorUtils.tools.vid_id_tools import *

switchOnVIDElectronIdProducer(process, DataFormat.MiniAOD)

# define which IDs we want to produce
my_id_modules = ['RecoEgamma.ElectronIdentification.Identification.mvaElectronID_Spring15_25ns_Trig_V1_cff']

#add them to the VID producer
for idmod in my_id_modules:
    setupAllVIDIdsInModule(process,idmod,setupVIDElectronSelection)

###############################
##### MET Uncertainities ######
###############################

##from PhysicsTools.PatUtils.tools.runMETCorrectionsAndUncertainties import runMetCorAndUncFromMiniAOD
#default configuration for miniAOD reprocessing, change the isData flag to run on data
#runMetCorAndUncFromMiniAOD(process, isData=False)#MC
##runMetCorAndUncFromMiniAOD(process, isData=True)#Data

#### the lines below remove the L2L3 residual uncertainties when processing data
#process.patPFMetT1T2Corr.jetCorrLabelRes = cms.InputTag("L3Absolute")
#process.patPFMetT1T2SmearCorr.jetCorrLabelRes = cms.InputTag("L3Absolute")
#process.patPFMetT2Corr.jetCorrLabelRes = cms.InputTag("L3Absolute")
#process.patPFMetT2SmearCorr.jetCorrLabelRes = cms.InputTag("L3Absolute")
#process.shiftedPatJetEnDown.jetCorrLabelUpToL3Res = cms.InputTag("ak4PFCHSL1FastL2L3Corrector")
#process.shiftedPatJetEnUp.jetCorrLabelUpToL3Res = cms.InputTag("ak4PFCHSL1FastL2L3Corrector")

#from PhysicsTools.PatUtils.tools.runType1PFMEtUncertainties import runType1PFMEtUncertainties
#runType1PFMEtUncertainties(process,addToPatDefaultSequence=False,
#                           photonCollection="slimmedPhotons",
#                           jetCollection="slimmedJets",
#                           electronCollection="slimmedElectrons",
#                           muonCollection="slimmedMuons",
#                           tauCollection="slimmedTaus")



####
# The N-tupliser/cutFlow
####

triggerStringName = 'HLT'

process.load("NTupliser.SingleTop.MakeTopologyNtuple_miniAOD_cfi")
process.makeTopologyNtupleMiniAOD.flavorHistoryTag=cms.bool(False) # change to false at your convenience
process.makeTopologyNtupleMiniAOD.runMCInfo=cms.bool(True) # prevent checking gen info
process.makeTopologyNtupleMiniAOD.runPUReWeight=cms.bool(True) #Run the reweighting for MC. I think I'm doing this right, but I might check anyway.
process.makeTopologyNtupleMiniAOD.triggerTag = cms.InputTag("TriggerResults","",triggerStringName) # or HLT, depends on file   

#settings to apply tight selection:
process.makeTopologyNtupleMiniAOD.minJetPt=cms.double(0.0)
process.makeTopologyNtupleMiniAOD.maxJetEta=cms.double(5.0)
process.makeTopologyNtupleMiniAOD.bDiscCut=cms.double(-1.0)
process.makeTopologyNtupleMiniAOD.minEleEt=cms.double(0.0)
process.makeTopologyNtupleMiniAOD.maxEleEta=cms.double(5.0)
process.makeTopologyNtupleMiniAOD.ignoreElectronID=cms.bool(False) ## if set to true will save all electrons, also those not passing electronID.
process.makeTopologyNtupleMiniAOD.eleCombRelIso=cms.double(0.15)
process.makeTopologyNtupleMiniAOD.maxEled0=cms.double(0.04)
process.makeTopologyNtupleMiniAOD.eleInterECALEtaLow=cms.double(1.4442)
process.makeTopologyNtupleMiniAOD.eleInterECALEtaHigh=cms.double(1.5660)
process.makeTopologyNtupleMiniAOD.minEleEtLooseZVeto=cms.double(0)
process.makeTopologyNtupleMiniAOD.minEleEtaLooseZVeto=cms.double(5)
process.makeTopologyNtupleMiniAOD.eleCombRelIsoLooseZVeto=cms.double(1.0)
process.makeTopologyNtupleMiniAOD.dREleJetCrossClean=cms.double(0.3)
process.makeTopologyNtupleMiniAOD.maxMuonEta=cms.double(2.4)
process.makeTopologyNtupleMiniAOD.minMuonPt=cms.double(20)
process.makeTopologyNtupleMiniAOD.maxMuonD0=cms.double(0.02)
process.makeTopologyNtupleMiniAOD.muonRelIsoTight=cms.double(0.2)
process.makeTopologyNtupleMiniAOD.muoNormalizedChi2=cms.double(10)
process.makeTopologyNtupleMiniAOD.muoNTrkHits=cms.double(11)
process.makeTopologyNtupleMiniAOD.muonECalIso=cms.double(4)
process.makeTopologyNtupleMiniAOD.muonHCalIso=cms.double(6)
process.makeTopologyNtupleMiniAOD.dREleGeneralTrackMatchForPhotonRej=cms.double(0.3)
process.makeTopologyNtupleMiniAOD.maxDistForPhotonRej=cms.double(0.04)
process.makeTopologyNtupleMiniAOD.maxDcotForPhotonRej=cms.double(0.03)
process.makeTopologyNtupleMiniAOD.fillAll=cms.bool(True)
process.makeTopologyNtupleMiniAOD.processingLoose=cms.bool(False)
#process.makeTopologyNtupleMiniAOD.btagParameterizationList = cms.vstring()
#process.makeTopologyNtupleMiniAOD.btagParameterizationMode = cms.vstring()
process.makeTopologyNtupleMiniAOD.runSwissCross = cms.bool(False)
#Don't actually do cuts
process.makeTopologyNtupleMiniAOD.doCuts=cms.bool(False) # if set to false will skip ALL cuts. Z veto still applies electron cuts.
process.makeTopologyNtupleMiniAOD.runCutFlow=cms.double(0)

#Make the inputs for the n-tupliser right.
process.makeTopologyNtupleMiniAOD.electronPFTag = cms.InputTag("slimmedElectrons")
process.makeTopologyNtupleMiniAOD.tauPFTag = cms.InputTag("slimmedTaus")
process.makeTopologyNtupleMiniAOD.muonPFTag = cms.InputTag("slimmedMuons")
process.makeTopologyNtupleMiniAOD.jetPFToken = cms.InputTag("slimmedJets")
process.makeTopologyNtupleMiniAOD.metPFTag = cms.InputTag("slimmedMETs")
process.makeTopologyNtupleMiniAOD.rhoToken = cms.InputTag("fixedGridRhoAll")                                            
process.makeTopologyNtupleMiniAOD.conversionsToken = cms.InputTag("reducedEgamma", "reducedConversions")

##electronIdMva Stuff.
## triggering MVA
process.makeTopologyNtupleMiniAOD.eleTrigMediumIdMap = cms.InputTag("egmGsfElectronIDs:mvaEleID-Spring15-25ns-Trig-V1-wp90")
process.makeTopologyNtupleMiniAOD.eleTrigTightIdMap = cms.InputTag("egmGsfElectronIDs:mvaEleID-Spring15-25ns-Trig-V1-wp90")
process.makeTopologyNtupleMiniAOD.trigMvaValuesMap = cms.InputTag("electronMVAValueMapProducer:ElectronMVAEstimatorRun2Spring15Trig25nsV1Values")
process.makeTopologyNtupleMiniAOD.trigMvaCategoriesMap = cms.InputTag("electronMVAValueMapProducer:ElectronMVAEstimatorRun2Spring15Trig25nsV1Categories")

# non-triggering MVA
process.makeTopologyNtupleMiniAOD.eleNonTrigMediumIdMap = cms.InputTag("egmGsfElectronIDs:mvaEleID-Spring15-25ns-nonTrig-V1-wp90")
process.makeTopologyNtupleMiniAOD.eleNonTrigTightIdMap = cms.InputTag("egmGsfElectronIDs:mvaEleID-Spring15-25ns-nonTrig-V1-wp80")
process.makeTopologyNtupleMiniAOD.nonTrigMvaValuesMap = cms.InputTag("electronMVAValueMapProducer:ElectronMVAEstimatorRun2Spring15NonTrig25nsV1Values")
process.makeTopologyNtupleMiniAOD.nonTrigMvaCategoriesMap = cms.InputTag("electronMVAValueMapProducer:ElectronMVAEstimatorRun2Spring15NonTrig25nsV1Categories")

## Source
process.source = cms.Source("PoolSource",
    fileNames = cms.untracked.vstring()
)

## Maximal Number of Events
process.maxEvents = cms.untracked.PSet( input = cms.untracked.int32(-1) )

process.source.fileNames = [
	#'root://xrootd.unl.edu//store/mc/RunIIFall15MiniAODv1/ZZTo4L_13TeV_powheg_pythia8/MINIAODSIM/PU25nsData2015v1_76X_mcRun2_asymptotic_v12-v1/00000/0C0945C1-86B2-E511-B553-0CC47A78A440.root',
	#'root://xrootd.unl.edu//store/mc/RunIIFall15MiniAODv2/tZq_ll_4f_13TeV-amcatnlo-pythia8_TuneCUETP8M1/MINIAODSIM/PU25nsData2015v1_76X_mcRun2_asymptotic_v12-v1/00000/000420F1-1DB8-E511-B547-0025905C4270.root',
	#'root://xrootd.unl.edu//store/mc/RunIIFall15MiniAODv2/TTJets_DiLept_TuneCUETP8M1_13TeV-madgraphMLM-pythia8/MINIAODSIM/PU25nsData2015v1_76X_mcRun2_asymptotic_v12-v1/00000/00845120-42B8-E511-985A-002618943970.root',
	## tZq synch files
	#'root://xrootd.unl.edu//store/mc/RunIIFall15MiniAODv2/tZq_ll_4f_13TeV-amcatnlo-pythia8_TuneCUETP8M1/MINIAODSIM/PU25nsData2015v1_76X_mcRun2_asymptotic_v12-v1/00000/000420F1-1DB8-E511-B547-0025905C4270.root',
	#'root://xrootd.unl.edu//store/mc/RunIIFall15MiniAODv2/tZq_ll_4f_13TeV-amcatnlo-pythia8_TuneCUETP8M1/MINIAODSIM/PU25nsData2015v1_76X_mcRun2_asymptotic_v12-v1/00000/1077310F-20B8-E511-803E-0025905C4328.root',
	#'root://xrootd.unl.edu//store/mc/RunIIFall15MiniAODv2/tZq_ll_4f_13TeV-amcatnlo-pythia8_TuneCUETP8M1/MINIAODSIM/PU25nsData2015v1_76X_mcRun2_asymptotic_v12-v1/00000/1CF21F55-1EB8-E511-B7AE-0025905C22AE.root',
	#'root://xrootd.unl.edu//store/mc/RunIIFall15MiniAODv2/tZq_ll_4f_13TeV-amcatnlo-pythia8_TuneCUETP8M1/MINIAODSIM/PU25nsData2015v1_76X_mcRun2_asymptotic_v12-v1/00000/20D40820-20B8-E511-9714-0025905AC876.root',
	#'root://xrootd.unl.edu//store/mc/RunIIFall15MiniAODv2/tZq_ll_4f_13TeV-amcatnlo-pythia8_TuneCUETP8M1/MINIAODSIM/PU25nsData2015v1_76X_mcRun2_asymptotic_v12-v1/00000/20FC89A4-1FB8-E511-86A7-0025905C4328.root',
	## WZ synch files
	#'root://xrootd.unl.edu//store/mc/RunIISpring15DR74/WZTo3LNu_TuneCUETP8M1_13TeV-powheg-pythia8/MINIAODSIM/Asympt25ns_MCRUN2_74_V9-v1/60000/008E7FBF-9218-E511-81E0-001E675A5244.root',
	#'root://xrootd.unl.edu//store/mc/RunIISpring15DR74/WZTo3LNu_TuneCUETP8M1_13TeV-powheg-pythia8/MINIAODSIM/Asympt25ns_MCRUN2_74_V9-v1/60000/0473AA1C-AE18-E511-A22A-A0040420FE80.root',
	#'root://xrootd.unl.edu//store/mc/RunIISpring15DR74/WZTo3LNu_TuneCUETP8M1_13TeV-powheg-pythia8/MINIAODSIM/Asympt25ns_MCRUN2_74_V9-v1/60000/0C4172B8-9218-E511-B9C9-001E675A58D9.root',
	#'root://xrootd.unl.edu//store/mc/RunIISpring15DR74/WZTo3LNu_TuneCUETP8M1_13TeV-powheg-pythia8/MINIAODSIM/Asympt25ns_MCRUN2_74_V9-v1/60000/1299A85E-9E18-E511-AE6C-A0040420FE80.root',
	#'root://xrootd.unl.edu//store/mc/RunIISpring15DR74/WZTo3LNu_TuneCUETP8M1_13TeV-powheg-pythia8/MINIAODSIM/Asympt25ns_MCRUN2_74_V9-v1/60000/20469B1E-9F18-E511-A402-0002C94CD12E.root',
	#'root://xrootd.unl.edu//store/mc/RunIISpring15DR74/WZTo3LNu_TuneCUETP8M1_13TeV-powheg-pythia8/MINIAODSIM/Asympt25ns_MCRUN2_74_V9-v1/60000/260EDE5C-9618-E511-9769-001517E74088.root',
	## ttZ synch files
	#'root://xrootd.unl.edu//store/mc/RunIIFall15MiniAODv2/TTZToLLNuNu_M-10_TuneCUETP8M1_13TeV-amcatnlo-pythia8/MINIAODSIM/PU25nsData2015v1_76X_mcRun2_asymptotic_v12-v1/60000/0C0B0AFB-D5DF-E511-BB3D-008CFAF0743A.root',
	#'root://xrootd.unl.edu//store/mc/RunIIFall15MiniAODv2/TTZToLLNuNu_M-10_TuneCUETP8M1_13TeV-amcatnlo-pythia8/MINIAODSIM/PU25nsData2015v1_76X_mcRun2_asymptotic_v12-v1/60000/1EB49C33-7DDF-E511-B80F-0090FAA57A50.root',
	#'root://xrootd.unl.edu//store/mc/RunIIFall15MiniAODv2/TTZToLLNuNu_M-10_TuneCUETP8M1_13TeV-amcatnlo-pythia8/MINIAODSIM/PU25nsData2015v1_76X_mcRun2_asymptotic_v12-v1/60000/428D2F9A-A9DF-E511-88E1-D067E5F91F71.root',
	#'root://xrootd.unl.edu//store/mc/RunIIFall15MiniAODv2/TTZToLLNuNu_M-10_TuneCUETP8M1_13TeV-amcatnlo-pythia8/MINIAODSIM/PU25nsData2015v1_76X_mcRun2_asymptotic_v12-v1/60000/66C4E906-9BDF-E511-8B9B-02163E00C780.root',
	#'root://xrootd.unl.edu//store/mc/RunIIFall15MiniAODv2/TTZToLLNuNu_M-10_TuneCUETP8M1_13TeV-amcatnlo-pythia8/MINIAODSIM/PU25nsData2015v1_76X_mcRun2_asymptotic_v12-v1/60000/802B0F92-7DDF-E511-B870-002590D0B04A.root',
	#'root://xrootd.unl.edu//store/mc/RunIIFall15MiniAODv2/TTZToLLNuNu_M-10_TuneCUETP8M1_13TeV-amcatnlo-pythia8/MINIAODSIM/PU25nsData2015v1_76X_mcRun2_asymptotic_v12-v1/60000/84D78733-8BDF-E511-BE44-02163E0138D7.root',
	#'root://xrootd.unl.edu//store/mc/RunIIFall15MiniAODv2/TTZToLLNuNu_M-10_TuneCUETP8M1_13TeV-amcatnlo-pythia8/MINIAODSIM/PU25nsData2015v1_76X_mcRun2_asymptotic_v12-v1/60000/9E1D98CF-7EDF-E511-953F-AC853D9DACE1.root',
	#'root://xrootd.unl.edu//store/mc/RunIIFall15MiniAODv2/TTZToLLNuNu_M-10_TuneCUETP8M1_13TeV-amcatnlo-pythia8/MINIAODSIM/PU25nsData2015v1_76X_mcRun2_asymptotic_v12-v1/60000/AA7BDF99-8ADF-E511-AFE3-02163E01315B.root',
	#'root://xrootd.unl.edu//store/mc/RunIIFall15MiniAODv2/TTZToLLNuNu_M-10_TuneCUETP8M1_13TeV-amcatnlo-pythia8/MINIAODSIM/PU25nsData2015v1_76X_mcRun2_asymptotic_v12-v1/60000/B03CEEC3-8ADF-E511-B5ED-02163E013ADF.root',
	#'root://xrootd.unl.edu//store/mc/RunIIFall15MiniAODv2/TTZToLLNuNu_M-10_TuneCUETP8M1_13TeV-amcatnlo-pythia8/MINIAODSIM/PU25nsData2015v1_76X_mcRun2_asymptotic_v12-v1/60000/B46C8814-7BDF-E511-AE26-00259073E496.root',
	## tt synch files
	'root://xrootd.unl.edu//store/mc/RunIIFall15MiniAODv2/TTTo2L2Nu_13TeV-powheg/MINIAODSIM/PU25nsData2015v1_76X_mcRun2_asymptotic_v12_ext1-v1/00000/0024B479-17DC-E511-B25F-0025904CF758.root',
	'root://xrootd.unl.edu//store/mc/RunIIFall15MiniAODv2/TTTo2L2Nu_13TeV-powheg/MINIAODSIM/PU25nsData2015v1_76X_mcRun2_asymptotic_v12_ext1-v1/00000/00347F86-1BDC-E511-933C-0025905C95F8.root',
	'root://xrootd.unl.edu//store/mc/RunIIFall15MiniAODv2/TTTo2L2Nu_13TeV-powheg/MINIAODSIM/PU25nsData2015v1_76X_mcRun2_asymptotic_v12_ext1-v1/00000/0243D352-1CDC-E511-994B-0025905C3DD0.root',
	'root://xrootd.unl.edu//store/mc/RunIIFall15MiniAODv2/TTTo2L2Nu_13TeV-powheg/MINIAODSIM/PU25nsData2015v1_76X_mcRun2_asymptotic_v12_ext1-v1/00000/024B2AA3-1CDC-E511-A02F-0025905C96A4.root',
	'root://xrootd.unl.edu//store/mc/RunIIFall15MiniAODv2/TTTo2L2Nu_13TeV-powheg/MINIAODSIM/PU25nsData2015v1_76X_mcRun2_asymptotic_v12_ext1-v1/00000/027E1612-1BDC-E511-A1CC-0CC47A1E048C.root',
	'root://xrootd.unl.edu//store/mc/RunIIFall15MiniAODv2/TTTo2L2Nu_13TeV-powheg/MINIAODSIM/PU25nsData2015v1_76X_mcRun2_asymptotic_v12_ext1-v1/00000/02B71BCB-1EDC-E511-997C-0CC47A1DF652.root',
	'root://xrootd.unl.edu//store/mc/RunIIFall15MiniAODv2/TTTo2L2Nu_13TeV-powheg/MINIAODSIM/PU25nsData2015v1_76X_mcRun2_asymptotic_v12_ext1-v1/00000/02C19778-1DDC-E511-97FD-0025905C2CE4.root',
	'root://xrootd.unl.edu//store/mc/RunIIFall15MiniAODv2/TTTo2L2Nu_13TeV-powheg/MINIAODSIM/PU25nsData2015v1_76X_mcRun2_asymptotic_v12_ext1-v1/00000/02D16635-18DC-E511-BFC1-0025905C43EC.root',
	'root://xrootd.unl.edu//store/mc/RunIIFall15MiniAODv2/TTTo2L2Nu_13TeV-powheg/MINIAODSIM/PU25nsData2015v1_76X_mcRun2_asymptotic_v12_ext1-v1/00000/02EEBE0F-19DC-E511-8B79-00266CFEFC38.root',
	'root://xrootd.unl.edu//store/mc/RunIIFall15MiniAODv2/TTTo2L2Nu_13TeV-powheg/MINIAODSIM/PU25nsData2015v1_76X_mcRun2_asymptotic_v12_ext1-v1/00000/043FE20F-1BDC-E511-B0D2-0CC47A1DF80A.root',
        ]

from PhysicsTools.PatAlgos.patEventContent_cff import *
from PhysicsTools.PatAlgos.patEventContent_cff import patEventContentNoCleaning

process.out = cms.OutputModule("PoolOutputModule",
                               fileName = cms.untracked.string('patTuple.root'),
                               ## save only events passing the full path
                               #SelectEvents = cms.untracked.PSet( SelectEvents = cms.vstring('p') ),
                               ## save PAT output; you need a '*' to unpack the list of commands
                               outputCommands = cms.untracked.vstring('drop *', *patEventContentNoCleaning )
                               )

process.out.outputCommands += patEventContent
process.out.outputCommands += patTriggerEventContent
process.out.outputCommands += patExtraAodEventContent
process.out.outputCommands += cms.untracked.vstring('keep *_flavorHistoryFilter_*_*','keep *_TriggerResults_*_*','keep *_selectedPat*_*_*', 'keep *_*goodOfflinePrimaryVertices*_*_*','keep double_*_rho_*', 'keep patMuons_*_*_*', 'keep *MET*_*_*_*', 'keep *_*MET*_*_*')


#PAT output and various other outpath stuff which is a bit dumb coz I'm probably not even gonna use the outpath. Nevermind.
process.out.fileName = cms.untracked.string('Data_out.root')

#NTuple output
process.TFileService = cms.Service("TFileService", fileName = cms.string('Data_test.root') )
process.options.wantSummary = False
process.out.SelectEvents = cms.untracked.PSet(SelectEvents = cms.vstring('p'))

#Removing pat output (coz we really don't need it now)
#del process.out

process.p = cms.Path(
    process.filtersSeq *
#    process.producePatPFMETCorrections *
    process.egmGsfElectronIDSequence *
    process.makeTopologyNtupleMiniAOD
    )

process.schedule = cms.Schedule( process.p )

process.outpath = cms.EndPath( process.out )
