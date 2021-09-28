# imports ##########################################################
import time
import TerrainStageSimulator.src.color_print as TCpr
#from tabulate import tabulate
####################################################################

# timingDict:
#   timingDict['[self._className]_[name]'] = {minTime, maxTime, avgTime, numSamples, accumlatedTime, newTic, ticTime}

####################################################################
class CTimingModule():
    """docstring for CTimingModule"""
    def __init__(self):
        super(CTimingModule, self).__init__()

    def _initTiming(self,name):
        self._className = name
        self._timingDict = {}
        self._timingTables = []

    def _tic(self,name):
        # get current time
        now = time.time()

        # build up name of key
        keyName = self._className + '_' + name

        # check if entry of key already exist
        if keyName in self._timingDict.keys():
            self._timingDict[keyName]['newTic'] = True
            self._timingDict[keyName]['ticTime'] = now
        else:
            # new entry
            self._timingSample = {}
            self._timingSample['numSamples'] = 0
            self._timingSample['newTic'] = True
            self._timingSample['ticTime'] = now
            self._timingDict[keyName] = self._timingSample

    def _toc(self,name):
        # get current time
        now = time.time()

        # build up name of key
        keyName = self._className + '_' + name

        # check if entry of key already exist
        if keyName in self._timingDict.keys():
            # check of tic was called before toc
            if self._timingDict[keyName]['newTic']:
                # calc delta time
                deltaTime = now - self._timingDict[keyName]['ticTime']
                # min time ####################################################
                if 'minTime' in self._timingDict[keyName].keys():
                    if deltaTime < self._timingDict[keyName]['minTime']:
                        self._timingDict[keyName]['minTime'] = deltaTime
                else:
                    self._timingDict[keyName]['minTime'] = deltaTime
                #############################################################

                # max time ####################################################
                if 'maxTime' in self._timingDict[keyName].keys():
                    if deltaTime > self._timingDict[keyName]['maxTime']:
                        self._timingDict[keyName]['maxTime'] = deltaTime
                else:
                    self._timingDict[keyName]['maxTime'] = deltaTime
                #############################################################

                # average time ####################################################
                self._timingDict[keyName]['numSamples'] += 1
                if 'average' in self._timingDict[keyName].keys():
                    self._timingDict[keyName]['accumlatedTime'] += deltaTime
                    self._timingDict[keyName]['average'] = self._timingDict[keyName]['accumlatedTime']/self._timingDict[keyName]['numSamples']
                else:
                    self._timingDict[keyName]['average'] = deltaTime
                    self._timingDict[keyName]['accumlatedTime'] = deltaTime
                #############################################################

                # clean up ##################
                self._timingDict[keyName]['newTic'] = False
                self._timingDict[keyName]['ticTime'] = -1
                ##################

            else:
                print('ERROR: call tic before toc!')
            
        else:
            print('ERROR: call tic before toc!')


    def get_timing(self):
        return self._timingDict

    def _add_new_timing_table(self,newTimingTable):
        self._timingTables.append(newTimingTable)

    def _print_timing_tables(self):
        # add own timing table
        self._timingTables.append(self._timingDict)

        # header for tables
        timingHeaders=['timingAgent', 'avgTime[sec]', 'minTime[sec]', 'maxTime[sec]', 'numSamples']

        # go through timing tables and print timing information
        TCpr.prOrange('##### Timming Tables ####################################################################\n')
        for tableEntry in self._timingTables:
            # go through timing agents of entry of timing table
            tableRows = []
            for key in tableEntry:
                print("key: ", key)
                print("tableEntry[key]['average']: ", tableEntry[key]['average'])
                print("tableEntry[key]['minTime']: ", tableEntry[key]['minTime'])
                print("tableEntry[key]['maxTime']: ", tableEntry[key]['maxTime'])
                print("tableEntry[key]['numSamples']: ", tableEntry[key]['numSamples'])
                #tableSingleRow = [key ,tableEntry[key]['average'], tableEntry[key]['minTime'], tableEntry[key]['maxTime'], tableEntry[key]['numSamples']]
                #tableRows.append(tableSingleRow)
            # print table
            #TCpr.prOrange(tabulate(tableRows,headers=timingHeaders))
            TCpr.prOrange('##########################################################################################\n')