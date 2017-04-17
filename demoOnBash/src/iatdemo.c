// iatdemo.c : Defines the entry point for the console application.
//
/*********
语音听写demo
*********/

#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <errno.h>
#include <unistd.h>

#include "include/qisr.h"
#include "include/msp_cmn.h"
#include "include/msp_errors.h"

void run_iat(const char* src_wav_filename ,  const char* param)
{
	char rec_result[1024] = {0};
	const char *sessionID = NULL;
	FILE *f_pcm = NULL;
	char *pPCM = NULL;
	int lastAudio = 0 ;
	int audStat = MSP_AUDIO_SAMPLE_CONTINUE ;
	int epStatus = MSP_EP_LOOKING_FOR_SPEECH;
	int recStatus = MSP_REC_STATUS_SUCCESS ;
	long pcmCount = 0;
	long pcmSize = 0;
	int errCode = 0 ;
	int ret = 0;
	
	f_pcm = fopen(src_wav_filename, "rb");
	if (NULL != f_pcm) //读取音频文件
	{
		fseek(f_pcm, 0, SEEK_END);
		pcmSize = ftell(f_pcm);
		fseek(f_pcm, 0, SEEK_SET);
		pPCM = (char *)malloc(pcmSize);
		fread((void *)pPCM, pcmSize, 1, f_pcm);
		fclose(f_pcm);
		f_pcm = NULL;
	}

	fprintf(stderr, "iat begin ......\n");
	sessionID = QISRSessionBegin(NULL, param, &errCode);//开始一路会话
	if (errCode != 0)
	{
		fprintf(stderr, "QISRSessionBegin Failed , error code %d\n",errCode);
	}
	while (1) 
	{
		unsigned int len = 6400;
		unsigned int audio_len = 6400;
		if (pcmSize < 12800) 
		{
			len = pcmSize;
			lastAudio = 1;//音频长度小于12800
		}
		audStat = MSP_AUDIO_SAMPLE_CONTINUE;//有后继音频
		if (pcmCount == 0)
			audStat = MSP_AUDIO_SAMPLE_FIRST;
		if (len<=0)
		{
			break;
		}
		fprintf(stderr, "csid=%s,count=%d,aus=%d,",sessionID,pcmCount/audio_len,audStat);
		ret = QISRAudioWrite(sessionID, (const void *)&pPCM[pcmCount], len, audStat, &epStatus, &recStatus);//写音频
		fprintf(stderr, "eps=%d,rss=%d,ret=%d\n",epStatus,recStatus,errCode);
		if (ret != 0)
		{
			fprintf(stderr, "QISRAudioWirte Failed ,error code %d\n",ret);
			break;
		}
		
		pcmCount += (long)len;
		pcmSize -= (long)len;
		if (recStatus == MSP_REC_STATUS_SUCCESS) 
		{
			const char *rslt = QISRGetResult(sessionID, &recStatus, 0, &errCode);//服务端已经有识别结果，可以获取
			if (errCode !=0)
			{
				fprintf(stderr, "QISRGetResult Failed ,error code %d\n",errCode);
			}
			if (NULL != rslt)
			{
				strcat(rec_result,rslt);
			}
		}
		if (epStatus == MSP_EP_AFTER_SPEECH)
			break;
		usleep(150*1000);//模拟人说话时间间隙
	}
	QISRAudioWrite(sessionID, (const void *)NULL, 0, MSP_AUDIO_SAMPLE_LAST, &epStatus, &recStatus);//告知服务端已检测到最后一块音频
	free(pPCM);
	pPCM = NULL;
	while (recStatus != MSP_REC_STATUS_COMPLETE && 0 == errCode) 
	{
		const char *rslt = QISRGetResult(sessionID, &recStatus, 0, &errCode);//获取结果
		if (errCode !=0)
		{
			fprintf(stderr, "QISRGetResult Failed ,error code %d\n",errCode);
		}
		if (NULL != rslt)
		{
			strcat(rec_result,rslt);
		}
		usleep(150*1000);
	}
	ret = QISRSessionEnd(sessionID, NULL);
	if (ret != 0)
	{
		fprintf(stderr, "QISRSessionEnd Failed ,error code %d\n",ret);
	}
	fprintf(stderr, "iat end ......\n");
	fprintf(stderr, "=============================================================\n");
	fprintf(stderr, "The result is: %s\n",rec_result);
	fprintf(stderr, "=============================================================\n");
	printf("%s\n", rec_result);

}

int main(int argc, char* argv[])
{
    ///APPID请勿随意改动
	const char* login_configs = "appid = 300009334185";//登录参数
	const char* param2 = "sub=iat,auf=audio/L16;rate=16000,aue=speex-wb,ent=sms16k,rst=plain,rse=utf8";
	
	fprintf(stderr, "********语音听写demo********\n");
	int ret = MSPLogin(NULL, NULL, login_configs);
	if ( ret != MSP_SUCCESS )
	{
		fprintf(stderr, "MSPLogin failed , Error code %d.\n",ret);
		goto exit ;
	}
	run_iat(argv[1] ,  param2);

	exit:
	MSPLogout();//退出登录
	return 0;
}

