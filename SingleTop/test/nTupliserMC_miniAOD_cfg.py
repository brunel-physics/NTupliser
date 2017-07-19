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
process.GlobalTag.globaltag = cms.string('80X_mcRun2_asymptotic_2016_TrancheIV_v8')

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

###############################
########Jet corrections########
###############################

from PhysicsTools.PatAlgos.tools.jetTools import updateJetCollection

updateJetCollection(
   process,
   jetSource = cms.InputTag('slimmedJets'),
   labelName = 'UpdatedJEC',
   jetCorrections = ('AK4PFchs', cms.vstring(['L1FastJet', 'L2Relative', 'L3Absolute']), 'None'),
)

process.jetCorrection = cms.Sequence( process.patJetCorrFactorsUpdatedJEC * process.updatedPatJetsUpdatedJEC )

###############################
########EGM Regression#########
###############################

from EgammaAnalysis.ElectronTools.regressionWeights_cfi import regressionWeights
process = regressionWeights(process)
process.load('EgammaAnalysis.ElectronTools.regressionApplication_cff')

###############################
#########EGM Smearing##########
###############################

process.load('EgammaAnalysis.ElectronTools.calibratedPatElectronsRun2_cfi')

process.RandomNumberGeneratorService = cms.Service("RandomNumberGeneratorService",
                                                   calibratedPatElectrons  = cms.PSet( initialSeed = cms.untracked.uint32(81),
                                                                                       engineName = cms.untracked.string('TRandom3'),
                                                                                       ),
                                                   )

process.selectedSlimmedElectrons = cms.EDFilter("PATElectronSelector",     ## this protects against a crash in electron calibration     ## due to electrons with eta > 2.5     
                                                src = cms.InputTag("slimmedElectrons"),      
                                                cut = cms.string("pt>5 && abs(eta)<2.5") ) 

calibratedPatElectrons = cms.EDProducer("CalibratedPatElectronProducerRun2",
                                        
                                        # input collections
                                        electrons = cms.InputTag('selectedSlimmedElectrons'),
                                        gbrForestName = cms.string("gedelectron_p4combination_25ns"),
                                        
                                        # data or MC corrections
                                        # if isMC is false, data corrections are applied
                                        isMC = cms.bool(True),
                                        
                                        # set to True to get special "fake" smearing for synchronization. Use JUST in case of synchronization
                                        isSynchronization = cms.bool(False),

                                        correctionFile = cms.string("Moriond2017_JEC")
                                        )

process.selectedElectrons = cms.EDFilter("PATElectronSelector",
    src = cms.InputTag("calibratedPatElectrons"),
    cut = cms.string("pt>5 && abs(eta)")
                                         )

###############################
###### Electron ID ############
###############################

from PhysicsTools.SelectorUtils.tools.vid_id_tools import *

switchOnVIDElectronIdProducer(process, DataFormat.MiniAOD)

# define which IDs we want to produce
my_id_modules = ['RecoEgamma.ElectronIdentification.Identification.mvaElectronID_Spring15_25ns_Trig_V1_cff',
                 'RecoEgamma.ElectronIdentification.Identification.cutBasedElectronID_Summer16_80X_V1_cff']

#add them to the VID producer
for idmod in my_id_modules:
    setupAllVIDIdsInModule(process,idmod,setupVIDElectronSelection)

process.load("RecoEgamma.ElectronIdentification.ElectronIDValueMapProducer_cfi")
#process.electronIDValueMapProducer.srcMiniAOD = cms.InputTag('selectedElectrons')
process.electronIDValueMapProducer.srcMiniAOD = cms.InputTag('slimmedElectrons')
process.load("RecoEgamma.ElectronIdentification.ElectronMVAValueMapProducer_cfi")
#process.electronMVAValueMapProducer.srcMiniAOD = cms.InputTag('selectedElectrons')
process.electronMVAValueMapProducer.srcMiniAOD = cms.InputTag('slimmedElectrons')

###############################
##### MET Uncertainities ######
###############################

from PhysicsTools.PatUtils.tools.runMETCorrectionsAndUncertainties import runMetCorAndUncFromMiniAOD

## If you only want to re-correct and get the proper uncertainties
#runMetCorAndUncFromMiniAOD(process,
#                           isData=False,
#                           )

# If you would like to re-cluster and get the proper uncertainties
runMetCorAndUncFromMiniAOD(process,
                           isData=False,
#                           pfCandColl=cms.InputTag("packedPFCandidates"),
#                           recoMetFromPFCs=True,
                           )


####
# The N-tupliser/cutFlow
####

process.load("NTupliser.SingleTop.MakeTopologyNtuple_miniAOD_cfi")
process.makeTopologyNtupleMiniAOD.flavorHistoryTag=cms.bool(False) # change to false at your convenience
process.makeTopologyNtupleMiniAOD.runMCInfo=cms.bool(True) # prevent checking gen info
process.makeTopologyNtupleMiniAOD.runPUReWeight=cms.bool(True) #Run the reweighting for MC. I think I'm doing this right, but I might check anyway.
process.makeTopologyNtupleMiniAOD.triggerToken = cms.InputTag("TriggerResults","","HLT") # or HLT, depends on file   

#settings to apply tight selection:
process.makeTopologyNtupleMiniAOD.minJetPt=cms.double(0.0)
process.makeTopologyNtupleMiniAOD.maxJetEta=cms.double(5.5)
process.makeTopologyNtupleMiniAOD.bDiscCut=cms.double(-1.0)
process.makeTopologyNtupleMiniAOD.minElePt=cms.double(9.0)
process.makeTopologyNtupleMiniAOD.maxEleEta=cms.double(2.7)
process.makeTopologyNtupleMiniAOD.eleRelIso=cms.double(0.50)
process.makeTopologyNtupleMiniAOD.maxMuonEta=cms.double(2.8)
process.makeTopologyNtupleMiniAOD.minMuonPt=cms.double(9.0)
process.makeTopologyNtupleMiniAOD.muonRelIso=cms.double(0.50)
process.makeTopologyNtupleMiniAOD.maxDistForPhotonRej=cms.double(0.04)
process.makeTopologyNtupleMiniAOD.maxDcotForPhotonRej=cms.double(0.03)
process.makeTopologyNtupleMiniAOD.fillAll=cms.bool(True)
#process.makeTopologyNtupleMiniAOD.btagParameterizationList = cms.vstring()
#process.makeTopologyNtupleMiniAOD.btagParameterizationMode = cms.vstring()
#Don't actually do cuts
process.makeTopologyNtupleMiniAOD.doCuts=cms.bool(False) # if set to false will skip ALL cuts. Z veto still applies electron cuts.

#Make the inputs for the n-tupliser right.
process.makeTopologyNtupleMiniAOD.electronPFToken = cms.InputTag("calibratedPatElectrons")
process.makeTopologyNtupleMiniAOD.tauPFTag = cms.InputTag("slimmedTaus")
process.makeTopologyNtupleMiniAOD.muonPFToken = cms.InputTag("slimmedMuons")
process.makeTopologyNtupleMiniAOD.jetPFToken = cms.InputTag("updatedPatJetsUpdatedJEC") # Originally slimmedJets, patJetsReapplyJEC is the jet collection with reapplied JECs
process.makeTopologyNtupleMiniAOD.metPFToken = cms.InputTag("slimmedMETs")
process.makeTopologyNtupleMiniAOD.rhoToken = cms.InputTag("fixedGridRhoFastjetAll")                                            
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
#	'root://cms-xrd-global.cern.ch//store/mc/RunIISummer16MiniAODv2/DYJetsToLL_M-50_TuneCUETP8M1_13TeV-amcatnloFXFX-pythia8/MINIAODSIM/PUMoriond17_HCALDebug_80X_mcRun2_asymptotic_2016_TrancheIV_v6-v1/50000/00312D7A-FEBD-E611-A713-002590DB923E.root',
#	'root://cms-xrd-global.cern.ch//store/mc/RunIISummer16MiniAODv2/THQ_Hincl_13TeV-madgraph-pythia8_TuneCUETP8M1/MINIAODSIM/PUMoriond17_80X_mcRun2_asymptotic_2016_TrancheIV_v6-v1/50000/02259D47-A8D1-E611-AED1-02163E019BED.root',
	'root://cms-xrd-global.cern.ch//store/mc/RunIISummer16MiniAODv2/tZq_ll_4f_13TeV-amcatnlo-pythia8/MINIAODSIM/PUMoriond17_80X_mcRun2_asymptotic_2016_TrancheIV_v6_ext1-v1/120000/04A3B6DA-91C0-E611-BFF9-002590E39D8A.root',
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
process.TFileService = cms.Service("TFileService", fileName = cms.string('MC.root') )
process.options.wantSummary = False
process.out.SelectEvents = cms.untracked.PSet(SelectEvents = cms.vstring('p'))

#Removing pat output (coz we really don't need it now)
#del process.out

process.p = cms.Path(
    process.regressionApplication *
    process.calibratedPatElectrons *
    process.jetCorrection *
    process.fullPatMetSequence *
    process.selectedElectrons *
    process.egmGsfElectronIDSequence *
    process.makeTopologyNtupleMiniAOD
    )

process.schedule = cms.Schedule( process.p )

process.outpath = cms.EndPath( process.out )


