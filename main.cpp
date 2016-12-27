#include "client.h"
int main()
{
   transfer("read","192.168.83.218:8000","/dev/shm/500M.file","/root/leaf/pytoc/download/","0","0","0","1000000000000");
   return 0;

}
