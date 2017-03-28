#include<stdio.h>
#include<stdlib.h>
#include<string.h>
#include</usr/include/mysql/mysql.h>

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

int update_bitmap(int ini_bit, int size, char *filename)
{
	int pro_bit=ini_bit/10;	
	int size_bit=size/10;
	int i;
	printf("Data block start at %dMB, size is %dMB (Block unit is 10MB)\n",ini_bit,size);
	if(size%10!=0){
		size_bit++;
	}	
	char *bitmap=(char *)malloc(pro_bit+size_bit+1);
	if(bitmap==NULL){
		exit(1);
	}
	memset(bitmap,'0',sizeof(char)*(pro_bit+size_bit));
	for(i=pro_bit;i<pro_bit+size_bit;i++){
		bitmap[i]='1';
	}
	printf("bitmap: %s\n",bitmap);
	int pathlen=strlen(filename);
	char *name=(char *)malloc(pathlen+1);
	splitname(filename,name);
	FILE *cf=fopen("DBConfig","r");
	char *p_u, *p_p, *p_s;
	if(cf==NULL){
		printf("No DBConfig file\n");
		exit(0);
	}
	fseek(cf,0,SEEK_END);
        int len=ftell(cf);
	fseek(cf,0,SEEK_SET);
	char *buf=(char *)malloc(len*sizeof(char)+1);
        fgets(buf,len+1,cf);
	if(strlen(buf)>=5&&(p_u=strtok(buf,"/\n"))&&(p_p=strtok(NULL,"@\n"))&&(p_s=strtok(NULL,"\n"))){
      		printf("%s  %s  %s\n",p_s, p_u, p_p);
		fclose(cf);
		MYSQL *t_mysql;
		MYSQL_ROW row; 
		MYSQL_RES *result;
		unsigned long *length;
		char *check="select bitmap from Cns_file_transform_metadata where path='%s' and name='%s'";
	       	char *bitmap_update="update Cns_file_transform_metadata set bitmap='%s' where path='%s' and name='%s'";
     		char sql_check[1024];
		char sql_update[1024];
		sprintf(sql_check,check,filename,name);
		printf("sql_check is %s\n",sql_check);
		t_mysql=mysql_init(NULL);
        	if(t_mysql==NULL){
                	printf("mysql connection inition failed\n");
                	exit(1);
        	}
      		if(NULL==mysql_real_connect(t_mysql,p_s,p_u,p_p,"cns_db",0,NULL,0)){
               		printf("mysql connection failed\n");
                	exit(1);
        	}else
               	        printf("mysql connect successfully\n");	
		mysql_real_query(t_mysql,sql_check,strlen(sql_check));
		result=mysql_store_result(t_mysql);
	        row=mysql_fetch_row(result);
		length=mysql_fetch_lengths(result);
		if(length[0]!=0){
			int max=strlen(bitmap)>length[0]?strlen(bitmap):length[0];
			int temp;
			char *bitmap_new=(char *)malloc(max+1);
			for(temp=0;temp<max;temp++){
				if(bitmap[temp]=='1'||row[0][temp]=='1'){
					bitmap_new[temp]='1';
				}else
					bitmap_new[temp]='0';
			}
			bitmap_new[max]='\0';	
			sprintf(sql_update,bitmap_update,bitmap_new,filename,name);
		}else{
			sprintf(sql_update,bitmap_update,bitmap,filename,name);
		}
		printf("update_sql is %s\n",sql_update);
        	int a;
        	if(a=mysql_real_query(t_mysql,sql_update,strlen(sql_update))!=0){
                	printf("bitmap_update failed\n");
			mysql_close(t_mysql);
                	return 1;
        	}else
                	printf("bitmap_update successfully\n");
			mysql_close(t_mysql);
			return 0;
	}else{
		printf("ERROR in DBCONFIG\n");
		return 1;
	}
}
