#include "client.h"
int main()
{
   transread("202.122.37.90:28001","/root/leaf/pytoc/upload/night.mkv","/root/leaf/","0","0","0","1000000000000");
   //transupload("202.122.37.90:28001","/root/leaf/night.mkv","/root/leaf/pytoc/upload/night.mkv");
   return 0;

}
