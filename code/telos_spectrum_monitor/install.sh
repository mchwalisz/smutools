#!/bin/bash

USBDEV=$1
NEW_FREQUENCY_VECTOR=$2
USER_DESCRIPTION=$3
SF_PORT=`expr ${USBDEV: -1} + 9002`
SF_CMD="$TOSDIR/../support/sdk/c/sf/sf $SF_PORT $USBDEV 115200"
#SF_CMD="java net.tinyos.sf.SerialForwarder -comm serial@$USBDEV:115200 -no-gui -port $SF_PORT"


# we should always check if there are SF that are waiting on unpopulated USB-devices -> kill them!
USED_DEVTTYUSB=`motelist | grep /dev/ttyUSB | awk '{print $2}'`;
for i in $(seq 0 10)
do
  CHECK_DEVTTYUSB=/dev/ttyUSB$i
  MATCH=`expr match "$USED_DEVTTYUSB" ".*$CHECK_DEVTTYUSB.*"`
  if [[ $MATCH -eq 0 ]]
  then
    SFPID=`ps aux | grep support/sdk/c/sf/sf | grep $CHECK_DEVTTYUSB | awk '{print $2}'`
    if [[ -n $SFPID ]]
    then
      echo Killing unused serialforwarder on $CHECK_DEVTTYUSB with PID $SFPID
      kill $SFPID
    fi
  fi
done


if [[ $# != 2 && $# != 3 ]];
then
  echo "Usage: $0 <usbdev> <frequencies> [description]"  >&2
  echo "       where 'usbdev'      is the 'Device' entry for your telosb node as shown in the table below "  >&2
  echo "                           (or returned when running the 'motelist' script), e.g. /dev/ttyUSB0"  >&2
  echo "             'frequencies' is the list of frequencies (in MHz) between 2400 and 2480 that you want to scan. You can either enter a " >&2
  echo "                           comma-separated list, e.g. '2400,2405,2407'; or a range in the form X-Y, which expands to" >&2
  echo "                           X,X+2,X+4,...,Y (e.g. '2400-2408' will expand to '2400,2402,2404,2406,2408')."  >&2
  echo "             'description' is an optional description of the measurement that will by output to stdout (e.g. in top of the trace file), " >&2
  echo "                           and must be put in quotation marks" >&2
  echo "" >&2
  echo "Example: $0 /dev/ttyUSB0 2400-2408 \"Test measurement\""  >&2
  echo ""
  motelist
  exit
fi

if [[ ! -e $USBDEV ]]
then
  echo "Device $USBDEV does not exist (run 'motelist' to see all devices)."
  exit
fi

# check if it's a valid range, and if so: expand
if [ `expr match "$NEW_FREQUENCY_VECTOR" '24[0-9][0-9]-24[0-9][0-9]'` == 9 ]
then
FIRST=${NEW_FREQUENCY_VECTOR:0:4}     
LAST=${NEW_FREQUENCY_VECTOR:5:8}     
NEW_FREQUENCY_VECTOR=$FIRST
for (( i=$FIRST+2; i<=$LAST; i+=2 ))
  do
     NEW_FREQUENCY_VECTOR=$NEW_FREQUENCY_VECTOR,$i
 done
fi

# strip any whitespace from the input list
NEW_FREQUENCY_VECTOR=${NEW_FREQUENCY_VECTOR//[[:space:]]}

# check if number of chars make sense
if [ $(((${#NEW_FREQUENCY_VECTOR}+1) % 5)) != 0 ]
then
  echo "Incorrect input format! Exiting ..."
  exit
fi

TEST_VECTOR=$NEW_FREQUENCY_VECTOR,
for (( i=0; i<=(${#TEST_VECTOR}+1)-5; i+=5 ))
  do
    TMP=${TEST_VECTOR:$i:5}
    if [ `expr match "$TMP" '24[0-9][0-9],'` != 5 ]
    then
      echo "Incorrect input format for frequency '$TMP'! Exiting ..."
      exit
    fi
  done

export FREQUENCY_VECTOR=\{$NEW_FREQUENCY_VECTOR\};


SFPID=`ps aux | grep support/sdk/c/sf/sf | grep $USBDEV | awk '{print $2}'`
#SFPID=`ps aux | grep net.tinyos.sf.SerialForwarder | grep $USBDEV | awk '{print $2}'`
if [[ -n $SFPID ]]
then
  echo Killing previous serialforwarder with PID $SFPID >&2
  kill -9 $SFPID
fi

# make a temporary copy and install from there (so we don't interfere with other processes)
pushd . >&2
TMPDIR=`mktemp -d`
echo $TMPDIR >&2
cp Makefile $TMPDIR
cp *.nc $TMPDIR
cp *.c $TMPDIR
cp *.h $TMPDIR
cp -r twist_trace_parser* $TMPDIR
cp -r cc2420/ $TMPDIR
cp -r net/ $TMPDIR
cd $TMPDIR
make telosb install bsl,$USBDEV >&2 || { echo "command failed" >&2; make telosb install bsl,$USBDEV >&2; } 
rm -rf $TMPDIR
popd >&2

echo starting serialforwarder: $SF_CMD >&2
$SF_CMD &
INSTALL_TIME=`date '+DATE: %A, %m/%d/%y START-TIME: %H:%M:%S:%N (hr:min:sec:nanosec)'`
echo Measuring frequencies $FREQUENCY_VECTOR. >&2
echo All following output will now be displayed on stdout ... >&2

# this is the data that will end up on stdout:
echo \# Description: $USER_DESCRIPTION
echo \# $INSTALL_TIME
echo \# Frequencies \(in MHz\): $NEW_FREQUENCY_VECTOR
echo "# Data format: one line per sweep (scanning all frequencies in the order above), every entry represents "
echo "#              the average RF power (in dBm) measured on a frequency over a period of 192 microseconds."
CLASSPATH=.:./tinyos.jar:$CLASSPATH
java net.tinyos.tools.PrintfClient -comm sf@localhost:$SF_PORT

