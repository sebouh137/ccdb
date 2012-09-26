#include <iostream>
#include <strstream>

#include "CCDB/CalibrationGenerator.h"
#include "CCDB/MySQLCalibration.h"
#include "CCDB/SQLiteCalibration.h"
#include "CCDB/Providers/MySQLDataProvider.h"
#include "CCDB/Providers/SQLiteDataProvider.h"

using namespace std;

namespace ccdb
{

//______________________________________________________________________________
CalibrationGenerator::CalibrationGenerator()
{
}


//______________________________________________________________________________
CalibrationGenerator::~CalibrationGenerator()
{
}


//______________________________________________________________________________
Calibration* CalibrationGenerator::MakeCalibration( const std::string & connectionString, int run, const std::string& context )
{
	return MakeMySQLCalibration(connectionString, run, context);
}


//______________________________________________________________________________
Calibration* CalibrationGenerator::MakeMySQLCalibration( const std::string & connectionString, int run, const std::string& variation )
{
    //hash of requested variation
    string calibHash = GetCalibrationHash(connectionString, run, variation);

    //first we look maybe we already have such a calibration
    if(mCalibrationsByHash.find(calibHash) != mCalibrationsByHash.end())
    {
        return mCalibrationsByHash[calibHash];
    }

    //Ok, we have to create calibration
    //but lets see, maybe we at least have a MySQLDataProvider for this connectionString
    DataProvider *provider = NULL;
    if(mProvidersByUrl.find(connectionString) != mProvidersByUrl.end())
    {
        provider = static_cast<DataProvider *>(mProvidersByUrl[connectionString]);

        //lets see the provider is connected... if not it is useless
        if(provider!= NULL && !provider->IsConnected()) provider = NULL;
    }

	bool isMySql = false; //if false SQlite provider is used

    if(provider == NULL)
    {
		int typePos = connectionString.find("mysql://");
		if(typePos!=string::npos)
		{
			//It is mysql
			provider = new MySQLDataProvider();
			isMySql = true;
		}
		else
		{
			//is it sqlite then?
			int typePos = connectionString.find("sqlite://");
			if(typePos!=string::npos)
			{
				provider = new SQLiteDataProvider();
				isMySql = false;
			}
			else
			{
				//something wrong here!!!
				throw std::logic_error("Unknown connection string type. mysql:// and sqlite:// are only known types now ");
			}
		}        

        //and connect it
        if(!provider->Connect(connectionString))
        {
            //error hangling...
            vector<CCDBError *> errors = provider->GetErrors();
            string message;
            for(int i=0; i< errors.size(); i++)
            {
                message = errors[i]->GetMessage();
                message += " in ";
                message += errors[i]->GetErrorKey();
                message += " in ";
                message += errors[i]->GetSource();
                message += " in ";
                message += errors[i]->GetDescription();
                message += " in ";
            }

            delete provider;
            throw std::logic_error(message.c_str());
        }

        mProvidersByUrl[connectionString] = provider;
    }


    //now we create calibration
    Calibration * calib = (isMySql)? static_cast<Calibration*>(new MySQLCalibration()): static_cast<Calibration*>(new SQLiteCalibration());
    calib->UseProvider(provider, true);
    
    //add it to arrays
    mCalibrationsByHash[calibHash] = calib;
    mCalibrations.push_back(calib);

	return NULL;
}


//______________________________________________________________________________
string CalibrationGenerator::GetCalibrationHash( const std::string & connectionString, int run, const std::string& variation )
{   
     //gets string hash based on  connectionString, run, and variation
     //
     //The hash is used for storing Calibrations in calibrations hash table
     //so if user asks DCalibration which is already exists a new DCalibration 
     //will not be created once again but already created DCalibration is returned;

    //right now our hash will be just a summ of strings
    strstream strstrm;
    strstrm<<connectionString<<run<<variation;
    return strstrm.str();
}


//______________________________________________________________________________
bool CalibrationGenerator::CheckOpenable( const std::string & str)
{
    //right now we have only one provider, so it is simple
	if(str.find("mysql://")!= string::npos) return true;
	if(str.find("sqlite://")!= string::npos) return true;
    return false;
}


}

