import socket, subprocess, json
import time
import os.path
import numpy as np
import matplotlib.pyplot as pl
import sys



from telegram.ext import Updater

updater = Updater(token='334584323:AAFwCLmIrnfRgCtPFqYU3eNSMesq6b4yZzY')

dispatcher = updater.dispatcher

from telegram.ext import CommandHandler

global isWritingNetlist

isWritingNetlist = False
isPlotting = False

def start(bot, update):
    update.message.reply_text('Welcome to CircuitBot your everyday solution for easy Circuit Analysis\nSpeak Friend and Enter\n')


start_handler = CommandHandler('start', start)
dispatcher.add_handler(start_handler)


def echo(bot, update):
        if isWritingNetlist == False and isPlotting == False:
                bot.sendMessage(chat_id=update.message.chat_id, text="Please run the command /createNet to create your netlist\n"
                +"When done writing run the command /runSim to simulate netlist\n"
                +"For help writing the netlist use the command /help")
        
        elif isWritingNetlist == True and isPlotting == False:
                file = open('net' + str(update.message.chat_id) +'.txt','a+')
                file.write(update.message.text)
                file.write('\n')
                file.close()

        elif isPlotting == True and isWritingNetlist == False:
                if str(update.message.text) == 'Done' or str(update.message.text) == 'done':
                         proc = subprocess.Popen('rm ' + '\'output' + str(update.message.chat_id)+ '.txt\'' + ' ',stdout = subprocess.PIPE, stderr = subprocess.PIPE, shell=True)
                         bot.sendMessage(chat_id=update.message.chat_id, text='Thank You for using CircuitBot')
                         isPlotting = False
                   
                else:
                        plotter('output' + str(update.message.chat_id)+ '.txt','t',str(update.message.text),'figura'+str(update.message.chat_id)+'.png')
                        bot.send_photo(chat_id=update.message.chat_id, photo=open('figura'+str(update.message.chat_id)+'.png', 'rb'))
                        proc = subprocess.Popen('rm ' + '\'figura'+str(update.message.chat_id)+'.png\'' + ' ',stdout = subprocess.PIPE, stderr = subprocess.PIPE, shell=True)
                        bot.sendMessage(chat_id=update.message.chat_id, text='Would you like to plot another variable? Write done when finished!')


from telegram.ext import MessageHandler, Filters

echo_handler = MessageHandler([Filters.text], echo)
dispatcher.add_handler(echo_handler)

def createNet(bot, update, args):
        global isWritingNetlist
        proc = subprocess.Popen('rm -f ' + '\'net' + str(update.message.chat_id)+ '.txt\'' + ' ',stdout = subprocess.PIPE, stderr = subprocess.PIPE, shell=True)
        isWritingNetlist = True


createNet_handler = CommandHandler('createNet', createNet, pass_args=True)
dispatcher.add_handler(createNet_handler)


from telegram import InlineQueryResultArticle, InputTextMessageContent

def help(bot, update, args):
        bot.sendMessage(chat_id=update.message.chat_id, text='Write the components line by line\n\n'
        +'Start with the total number of nodes'
        +'Resistor:  R<name> <node+> <node-> <value>\n'
        +'VCCS:      G<name> <io+> <io-> <vi+> <vi-> <transcondutance>\n'
        +'VCVC:      E<name> <vo+> <vo-> <vi+> <vi-> <voltage gain>\n'
        +'CCCS:      F<nome> <io+> <io-> <ii+> <ii-> <current gain>\n'
        +'CCVS:      H<nome> <vo+> <vo-> <ii+> <ii-> <transresistence>\n'
        +'Current Source:   I<name> <io+> <io-> <parameters>\n'
        +'Voltage Source:   V<name> <vo+> <vo-> <parameters>\n'
        +'OP Amp:  O<name> <vo1> <vo2> <vi1> <vi2>\n'
        +'Inductor:   L<name> <node+> <node-> <indutance> [IC = <current>]\n'
        +'Capacitor: C<name> <node+> <node-> <Capacitance> [IC = <voltage>]\n\n\n'
        +'Source Paramters:\n'
        +'DC Source: DC <valor>\n'
        +'Sine Source: SIN <DC value> <amplitude> <frequency> <delay> <decay> <fase>\n'
        +'Pulse Source: PULSE <amplitude1> <amplitude2> <delay> <rise time> <fall time> <pulse width> <period> <number of cycles>\n'
        +'Last line Simulation Paramenters (This program uses an Adams-Moulton Integration):\n'
        +'.TRAN <final time> <time step> ADMO<order> <internal steps> UIC\n'
        +'Exemplo: \n'
        +'2\n'
        +'R1 1 2 1\n'
        +'R2 2 0 1\n'
        +'V1 1 0 DC 10\n'
        +'.TRAN 1 0.1 ADM1 1 1 UIC\n')


help_handler = CommandHandler('help', help, pass_args=True)
dispatcher.add_handler(help_handler)

def runSim(bot, update, args):
        global isWritingNetlist
        isWritingNetlist = False

        chat_id=update.message.chat_id
        execargs =  '\'net' + str(chat_id)+ '.txt\' \'output' + str(chat_id) + '.txt\''

        proc = subprocess.Popen('./exec2 ' + execargs + ' ',stdout = subprocess.PIPE, stderr = subprocess.PIPE, shell=True)
        (cmdOutput, cmdErr) = proc.communicate()
        try:
                cmdOutput = cmdOutput.decode('UTF-8').rstrip()
        except:
                pass
        try:
                cmdErr = cmdErr.decode('UTF-8').rstrip()
        except:
                pass
        
        if cmdErr:
                bot.sendMessage(chat_id=update.message.chat_id, text=cmdErr)

        proc = subprocess.Popen('rm ' + '\'net' + str(chat_id)+ '.txt\'' + ' ',stdout = subprocess.PIPE, stderr = subprocess.PIPE, shell=True)

        if cmdOutput == 'Analise concluida!':
                bot.sendMessage(chat_id=update.message.chat_id, text='Your Analysis was successful now to the plot!')
                bot.sendMessage(chat_id=update.message.chat_id, text='Run the command /plotAnalysis to plot your output or /getOutput to download simulator output file')
        else:
                bot.sendMessage(chat_id=update.message.chat_id, text='There was a simulation error! Please check your Netlist')    
                bot.sendMessage(chat_id=update.message.chat_id, text=cmdOutput)


runSim_handler = CommandHandler('runSim', runSim, pass_args=True)
dispatcher.add_handler(runSim_handler)

def plotAnalysis(bot, update, args):
        global isPlotting
        isPlotting = True
        f= open('output' + str(update.message.chat_id)+ '.txt',"r")
        lines= f.readlines()
        var_names = lines[0].split()

        plot_var = '%s' % ' , '.join(map(str, var_names[1:]));

        bot.sendMessage(chat_id=update.message.chat_id, text='These are the available variables -> ' + str(plot_var))
        bot.sendMessage(chat_id=update.message.chat_id, text="Which Variable would you like to plot?")


plotAnalysis_handler = CommandHandler('plotAnalysis', plotAnalysis, pass_args=True)
dispatcher.add_handler(plotAnalysis_handler)

def getOutput(bot, update, args):
        bot.send_document(chat_id=update.message.chat_id, document=open('output' + str(update.message.chat_id)+ '.txt', 'rb'))
        bot.sendMessage(chat_id=update.message.chat_id, text='Thank You for using CircuitBot')
        proc = subprocess.Popen('rm ' + '\'output' + str(update.message.chat_id)+ '.txt\'' + ' ',stdout = subprocess.PIPE, stderr = subprocess.PIPE, shell=True)


getOutput_handler = CommandHandler('getOutput', getOutput, pass_args=True)
dispatcher.add_handler(getOutput_handler)



def unknown(bot, update):
        bot.sendMessage(chat_id=update.message.chat_id, text="Unknown Command!! Please use an available command!")

unknown_handler = MessageHandler([Filters.command], unknown)
dispatcher.add_handler(unknown_handler)

updater.start_polling()

def plotter(nomeArquivo,var1,var2,nomeFigura):
    f= open(nomeArquivo,"r")

    lines= f.readlines()
    var_names = lines[0].split()

    xindex = var_names.index(var1)
    yindex = var_names.index(var2)
    values = []


    for line in lines[1:]: values.append(map(float, line.split())) 


    x= []
    y= []

    for index in range(0,len(values)):
        x.append(values[index][xindex])
        y.append(values[index][yindex])


    pl.xlabel(var1)
    pl.ylabel(var2)
    pl.grid()
    pl.plot(x, y)
    pl.title('Grafico '+var2+' por '+var1)
    pl.savefig(nomeFigura)

    f.close
