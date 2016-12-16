#include "client.h"
int main()
{
   transfer("read","192.168.83.218","/dev/shm/500M.file","0","0","138");
   return 0;

}
