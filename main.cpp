#include "client.h"
#include "client.cpp"
int main(int argc,char *argv[])
{  char *command = argv[1];
   //printf("%s\n",command);
   if(strcmp(command,"read")==0)
   {
   //transread("202.122.37.90:28003","/root/leaf/pytoc/upload/night.mkv","/root/leaf/","0","0","0","1000000000000");
   transread("202.122.37.90:28001","/root/leaf/pytoc/upload/test.log","/root/leaf/test.log","0","0","0","2097152");
   //transread("202.122.37.90:28001","/home/wangcong/leaf/upload/night.mkv","/root/leaf/night.mkv","0","0",0,800*1024*1024);
   }
   else if(strcmp(command,"upload")==0)
   {
   transupload("202.122.37.90:28001","/root/leaf/night.mkv","/home/wangcong/leaf/upload/night.mkv");
   }
   else 
   {printf("Error arguments!\n");}
   
   return 0;

}
