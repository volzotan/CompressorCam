struct CommunicationInterface {
  Stream* port;
  char* inputBuffer;
  String serialInputString;
  char serialCommand;
  int serialParam; 
  int serialParam2; 
};
