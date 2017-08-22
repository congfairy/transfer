#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <errno.h>
#include <mysql/mysql.h>

#define UNIT_SIZE (1024*1024)

MYSQL *l_mysql;

int splitname(char *path, char *basename){
        char *p;
        if (*path == 0 || *path != '/')  {
                return (-1);
        }
        /* silently remove trailing slashes */
        p = path + strlen (path) - 1;
        while (*p == '/' && p != path)
                *p = '\0';
        if ((p = strrchr (path, '/')) == NULL)
                p = path - 1;
        strcpy (basename, (*(p + 1)) ? p + 1 : "/");
        if (p <= path)  /* path in the form abc or /abc */
                p++;
        *p = '\0';
        return (0);
}

int sql_init(){
	FILE *mysql_config=fopen("/etc/NSCONFIG", "r");
	char *p_user, *p_passwd, *p_server;
	if(mysql_config==NULL){
		printf("DBConfig: %s\n",strerror(ENOENT ));
		return ENOENT ;
	}
	fseek(mysql_config, 0, SEEK_END);
	int len=ftell(mysql_config);
	fseek(mysql_config, 0, SEEK_SET);
	char *buf=(char *)malloc(len*sizeof(char));
	fgets(buf, len+1, mysql_config);
	fclose(mysql_config);
	if( strlen(buf)>=5 && (p_user=strtok(buf,"/\n")) && (p_passwd=strtok(NULL, "@\n")) && (p_server=strtok(NULL, "\n")) ){
                
                l_mysql=mysql_init(NULL);
                if(l_mysql==NULL){
                 	printf("mysql init failed: %s\n",strerror(EPIPE));
			return EPIPE ;
		}
                if(NULL==(l_mysql=mysql_real_connect(l_mysql,p_server,p_user,p_passwd,"cns_db",0,NULL,0))){
                	 printf("mysql connection: %s\n",strerror( ECONNREFUSED));
			 return ECONNREFUSED;
		}

	}else{
		printf("DBConfig: %s\n",strerror(EINVAL));
		return EINVAL;
	}
	free(buf);
	return 0;
}

int sql_close(){
	mysql_close(l_mysql);
	return 0;
}

int update_bitmap(off_t offset, size_t size, char *path, int filesize)
{
	if(offset<0||size<=0||!path||filesize<=0){
		printf("%s\n",strerror(EINVAL));
		return  EINVAL;
	}
	int sblock_num=offset/UNIT_SIZE;
	int eblock_num=(offset+size)/UNIT_SIZE;
	if((offset+size)%UNIT_SIZE!=0){
		eblock_num+=1;
	}
//	printf("offset=%d  size=%d  sblcok_num=%d  e_block_num=%d  UNIT_SIZE=%d  path=%s\n", offset, size, sblock_num, eblock_num, UNIT_SIZE, path);
	int res=0;
	if((res=sql_init())==0){
		MYSQL_ROW row;
		MYSQL_RES *result;
		unsigned long *length;
                char bitmap_update[]="update Cns_file_transform_metadata set bitmap='%s' where path='%s' and name='%s'";
		char sql_update[1024];

                char sql_check[1024];
                char *basename=(char *)malloc(strlen(path)+1);
                char check[]="select bitmap from Cns_file_transform_metadata where path='%s' and name='%s'";
                splitname(path, basename);
                sprintf(sql_check, check, path, basename);
                if(mysql_real_query(l_mysql,sql_check,strlen(sql_check))!=0){
                        printf("select failed no such file\n");
                        return ENOEXEC;
                }

                result=mysql_store_result(l_mysql);
                row=mysql_fetch_row(result);
		length=mysql_fetch_lengths(result);
		if(length[0]==0){
			printf("Bitmap: %s\n", strerror(ENODATA));
			return ENODATA;
		}else{
			int i;
			char *bitmap=(char *)malloc((length[0]+1)*sizeof(char));
			strcpy(bitmap, row[0]);
			for(i=sblock_num;i<eblock_num;i++){
				bitmap[i]='1';
			}
			sprintf(sql_update, bitmap_update, bitmap, path, basename);
			mysql_free_result(result);
			free(bitmap);
			free(basename);
//			printf("sql_for_update: %s\n",sql_update);
			if(mysql_real_query(l_mysql, sql_update, strlen(sql_update))!=0){
				printf("sql excute failed\n");
				return ENOEXEC;
			}
		}
	}
	sql_close();
	return res;
}
