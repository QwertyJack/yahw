// ttsdemo.c : Defines the entry point for the console application.

/*******
语音合成demo
******/
//
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <errno.h>
#include <unistd.h>

#include "include/qtts.h"
#include "include/msp_cmn.h"
#include "include/msp_errors.h"

typedef int SR_DWORD;
typedef short int SR_WORD ;

//音频头部格式
struct wave_pcm_hdr
{
	char            riff[4];                        // = "RIFF"
	SR_DWORD        size_8;                         // = FileSize - 8
	char            wave[4];                        // = "WAVE"
	char            fmt[4];                         // = "fmt "
	SR_DWORD        dwFmtSize;                      // = 下一个结构体的大小 : 16

	SR_WORD         format_tag;              // = PCM : 1
	SR_WORD         channels;                       // = 通道数 : 1
	SR_DWORD        samples_per_sec;        // = 采样率 : 8000 | 6000 | 11025 | 16000
	SR_DWORD        avg_bytes_per_sec;      // = 每秒字节数 : dwSamplesPerSec * wBitsPerSample / 8
	SR_WORD         block_align;            // = 每采样点字节数 : wBitsPerSample / 8
	SR_WORD         bits_per_sample;         // = 量化比特数: 8 | 16

	char            data[4];                        // = "data";
	SR_DWORD        data_size;                // = 纯数据长度 : FileSize - 44 
} ;

//默认音频头部数据
struct wave_pcm_hdr default_pcmwavhdr = 
{
	{ 'R', 'I', 'F', 'F' },
	0,
	{'W', 'A', 'V', 'E'},
	{'f', 'm', 't', ' '},
	16,
	1,
	1,
	16000,
	32000,
	2,
	16,
	{'d', 'a', 't', 'a'},
	0  
};

int text_to_speech(const char* src_text ,const char* des_path ,const char* params)
{
	struct wave_pcm_hdr pcmwavhdr = default_pcmwavhdr;
	const char* sess_id = NULL;
	int ret = -1;
	unsigned int text_len = 0;
	char* audio_data = NULL;
	unsigned int audio_len = 0;
	int synth_status = MSP_TTS_FLAG_STILL_HAVE_DATA;
	FILE* fp = NULL;

	
	if (NULL == src_text || NULL == des_path)
	{
		fprintf(stderr, "params is null!\n");
		return ret;
	}
	text_len = (unsigned int)strlen(src_text);
	fp = fopen(des_path,"wb");
	if (NULL == fp)
	{
		fprintf(stderr, "open file %s error\n",des_path);
		return ret;
	}
	fprintf(stderr, "TTS begin ......\n");
	sess_id = QTTSSessionBegin(params, &ret);
	if ( ret != MSP_SUCCESS )
	{
		fprintf(stderr, "QTTSSessionBegin failed Error code %d.\n",ret);
		return ret;
	}
	ret = QTTSTextPut(sess_id, src_text, text_len, NULL );
	if ( ret != MSP_SUCCESS )
	{
		fprintf(stderr, "QTTSTextPut failed Error code %d.\n",ret);
		QTTSSessionEnd(sess_id, "TextPutError");
		return ret;
	}
	fwrite(&pcmwavhdr, sizeof(pcmwavhdr) ,1, fp);
	while (1) 
	{
		const void *data = QTTSAudioGet(sess_id, &audio_len, &synth_status, &ret);
		if (NULL != data)
		{
			fwrite(data, audio_len, 1, fp);
		    pcmwavhdr.data_size += audio_len;//修正pcm数据的大小
			fprintf(stderr, "get audio data %d ....\n",strlen(data));
		}
		if (synth_status == MSP_TTS_FLAG_DATA_END || ret != 0) 
			break;
	}//合成状态synth_status取值可参考开发文档

	//修正pcm文件头数据的大小
	pcmwavhdr.size_8 += pcmwavhdr.data_size + 36;

	//将修正过的数据写回文件头部
	fseek(fp, 4, 0);
	fwrite(&pcmwavhdr.size_8,sizeof(pcmwavhdr.size_8), 1, fp);
	fseek(fp, 40, 0);
	fwrite(&pcmwavhdr.data_size,sizeof(pcmwavhdr.data_size), 1, fp);
	fclose(fp);

	ret = QTTSSessionEnd(sess_id, NULL);
	if ( ret != MSP_SUCCESS )
	{
		fprintf(stderr, "QTTSSessionEnd Error code %d.\n",ret);
	}
	fprintf(stderr, "\nTTS end ......\n");
	return ret;
}

int main(int argc, char* argv[])
{
	const char* login_configs = " appid = 300009334185";//登录参数
	const char* param = "vcn=xiaoyan,aue = speex-wb,auf=audio/L16;rate=16000,spd = 5,vol = 5, tte = utf8";//代码中为16k合成参数，8k音频合成参数：aue=speex,auf=audio/L16;rate=8000,其他参数意义参考参数列表

	fprintf(stderr, "*********语音合成demo********\n");
	int ret = MSPLogin(NULL, NULL, login_configs);
	if ( ret != MSP_SUCCESS )
	{
		fprintf(stderr, "MSPLogin failed , Error code %d.\n",ret);
		goto exit ;//登录失败，退出登录
	}

	FILE *fd = fopen(argv[1], "rb");
	if(!fd)
	{
		fprintf(stderr, "open the file is error!\n");
		exit(1);
	}
	fseek(fd, 0, SEEK_END);
	long lsize = ftell(fd);
	rewind(fd);

	char *buf = (char*) malloc (sizeof(char)*lsize);  
	if (!buf)  
	{  
		fputs ("Memory error",stderr);   
		exit (2);  
	} 

	size_t result = fread(buf,1,lsize,fd);  
	if (result != lsize)  
	{  
		fputs ("Reading error",stderr);  
		exit (3);  
	} 
	fclose(fd);

	//音频合成
	ret = text_to_speech(buf,argv[2],param);//音频合成
	if ( ret != MSP_SUCCESS )
	{
		fprintf(stderr, "text_to_speech: failed , Error code %d.\n",ret);
		goto exit ;//合成失败，退出登录
	}
	exit:
	MSPLogout();//退出登录
	free(buf);
	return 0;
}

