#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <time.h>
#include <sys/time.h>

#include "sfsource.h"
#include "serialpacket.h"
#include "serialprotocol.h"

#define nx_struct struct
#define nx_uint8_t int
#include "spectrummonitor.h"


// SAMPLING_PERIOD_IN_SECONDS must be the sampling period
// (defined in spectrummonitor.h)
#define SAMPLING_PERIOD_IN_SECONDS ((double) SAMPLING_PERIOD / (double) 32768)
#define MAX_NODE_ID 1000
int tmp[] = FREQUENCY_VECTOR;
#define NUM_SAMPLES_PER_PACKET (sizeof(tmp)/sizeof(int))

uint32_t currentTraceFileLine = 0;
int MAX_PACKET_SIZE = 512;

void hexprint(uint8_t *packet, int len)
{
  int i;
  for (i = 0; i < len; i++)
    printf("0x%02X, ", packet[i]);
}

void charprint(uint8_t *packet, int len)
{
  int i;
  for (i = 0; i < len; i++)
    printf("%c", packet[i]);
}

char convert_hexbyte(char *cptr) {
  // from: http://www.programmersheaven.com/download/3180/download.aspx
	char retval;
	char nbl;
	int shift;
	
	retval = 0;
	for( shift = 4; shift >= 0; shift -= 4 ) {
		if ((*cptr >= '0') && (*cptr <= '9')) {
			nbl = *cptr - '0';
		} else {
			if ((*cptr >= 'A') && (*cptr <= 'F')) {
				nbl = *cptr - 'A' + 10;		
      } else if ((*cptr >= 'a') && (*cptr <= 'f')) {
				nbl = *cptr - 'a' + 10;		
			} else {
        fprintf(stderr, "Packet content contains incorrect character %c in line %d\n", *cptr, currentTraceFileLine);
        exit(-1);
			}
		}
		++cptr;
		retval |= (nbl << shift);
	}
	return( retval );
}

void read_twist_trace_packet(FILE *fp, void *packet, int *len, int *sf_nodeID, double *packetTime)
{
  // format is: timestamp [double], sf_nodeID [int], packet content [hex] 
  unsigned char l;
  int i;
  char content[MAX_PACKET_SIZE], c;

  do {
    if (feof(fp)){
      *len = 0;
      return;
    }
    c = fgetc(fp);
    if (c == '#'){
      // skip comment
      if (fgets(content, sizeof(content), fp) == NULL){
        fprintf(stderr, "Line in trace file too long!\n");
        exit(-1);
      }
      printf("skipping line: %s", content); 
      currentTraceFileLine++;
    } else {
      ungetc(c, fp);
      break; // c != '#'
    }
  } while (1);
  i=fscanf (fp, "%lf", packetTime);
  i=fscanf (fp, "%d", sf_nodeID);
  i=fscanf (fp, "%s", content);
  if (fgetc(fp) != 0x0A) { // line break
    fprintf(stderr, "There is no line break after packet content in line %d!\n", currentTraceFileLine);
    exit(-1);
  }
  if (*len < strlen(content) / 2){
    *len = 0;
    return;
  } else
    *len = strlen(content) / 2;
  for (i=0; i<*len; i++)
    ((char*) packet)[i] = convert_hexbyte(content + 2*i);
  currentTraceFileLine++;
}


int main(int argc, char **argv)
{
  int fd, numChannels, numWritten=0, i, numTotalLines=0, senderSeqNo=0;
  FILE *infp = NULL;
  struct tm *local;
  time_t t = time(NULL);
  local = localtime(&t);
  double fractionDone = 0;
  char buf[1000];
  int fresh = 1;
  FILE *allOutfp[MAX_NODE_ID+1] = {NULL};

  if (argc != 3) {
    fprintf(stderr, "Usage: %s <TWIST_trace_file> <output_directory>\n", argv[0]);
    exit(-1);
  } else {
    infp=fopen(argv[1],"r");
    if (infp == NULL){
      printf("Error: cannot open (read) %s\n",argv[1]); 
      exit(-1); 
    }
  }

  printf("%s", asctime(local)); 
  printf("Reading input from %s\n", argv[1]); 

  for (;;)
  {
    int len = MAX_PACKET_SIZE, i, sf_nodeID = 0;
    double packetTime;
    uint8_t buffer[MAX_PACKET_SIZE];
    uint8_t *packet = buffer;
    FILE *outfp = NULL;
   
    read_twist_trace_packet(infp, packet, &len, &sf_nodeID, &packetTime);
    if (sf_nodeID > MAX_NODE_ID){
      printf("Node ID is too big: %d\n",sf_nodeID); 
      exit(-1); 
    }
    len -=2; // the last two payload bytes seem to be PRINTF specific!

    if (!len){
      printf("Error: invalid packet size!\n"); 
      exit(0);
    }

    if (len >= 1 + SPACKET_SIZE &&
        packet[0] == SERIAL_TOS_SERIAL_ACTIVE_MESSAGE_ID)
    {
      tmsg_t *msg;
      uint8_t amID;
      char filename[sizeof(argv[2])+10] = {0};

      msg = new_tmsg(packet + 1 + SPACKET_SIZE, len - 1);
      outfp = allOutfp[sf_nodeID];

      if (outfp == NULL) {
        sprintf(filename, "%s/%d.txt", argv[2], sf_nodeID);
        allOutfp[sf_nodeID] = fopen(filename,"w");
        outfp = allOutfp[sf_nodeID];
        fresh = 1;
        if (outfp == NULL){
          printf("Error: cannot write to file: %s\n",filename); 
          exit(-1); 
        }
      }

      if (!msg){
        printf("Error: msg is NULL !!!\n");
        exit(0);
      } else if (len < 8) {
        printf("serial packet len too small: %d !!!\n", len);
        exit(0);
      }

      amID = packet[7];
      if (amID != AM_PRINTF_MSG){
        printf("unknown AM id: %d!\n", amID);
        exit(1);
      } else {
        int i;
        char str[NUM_SAMPLES_PER_PACKET*10];
        for (i = SPACKET_SIZE+1; i < len && packet[i] != 0; i++)
          sprintf(&str[i-(SPACKET_SIZE+1)],"%c", packet[i]);
        str[i] = 0; // null-terminate string
        fprintf(outfp,"%lf %s", packetTime - (NUM_SAMPLES_PER_PACKET*SAMPLING_PERIOD_IN_SECONDS), str);
      }
      free(msg);

    } else {
      printf("non-AM packet: ");
      hexprint(packet, len);
    }
  }
  fflush(stdout);
}



