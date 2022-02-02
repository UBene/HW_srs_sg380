//
// Description:	Reverse Engineering the slicer IDL .ice file (based on aist_resources/remote_ctrl.lua qnami macro)
// Author: 		Benedikt Ursprung
// Date: 		Dec-02-2021
//



module RemoteSpmRPC
{
    interface RemoteSpm 
    {
        void setProperty(string prop, string val);
        void setAdapter(string name, string identity, string params);
        void setServer(string server)
        void start();
        void destroy();
        int errorsCnt();
        int error();
        bool isIdle();
        bool isConnecting();
        bool isConnected();
        bool isDisconnected();
        void callSlot(string slot);
        void callSlotOne(sting index, string slot);
        void callSlotAll(string slot);
        void sendArgs(string slot);
        void clientsUpdate();
        bool clientUpdated();
        int clientsCnt();
        int clients();
        bool clientValid(string index);
        int selfIndex();
       	list getArgs(strong slot);           
    }
}
