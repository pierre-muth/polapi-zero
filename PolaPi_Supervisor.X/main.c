/****************
 * File:   main.c
 * Author: muth
 * chip: PIC16F1829
 * Created on July 22, 2017, 9:47 AM
 * 
 * - PolaPi supervisor -
 * Splash screen
 * Battery ADC
 * Startup authorisation
 * 
 *          -01 VDD *    VSS 20-
 *     SDO2 -02 RA5      RA0 19-
 *      CS2 -03 RA4      RA1 18- LED   
 *          -04 RA3      RA2 17- AN2
 *          -05 RC5      RC0 16-
 *          -06 RC4      RC1 15-
 *          -07 RC3      RC2 14-
 *          -08 RC6      RB4 13- SDA1
 *          -09 RC7      RB5 12- SDI2
 *     SCK2 -10 RB7      RB6 11- SCL1
 * 
 ****************/


#include <xc.h>
#include "logo.h"

// CONFIG1
#pragma config FOSC = INTOSC    // Oscillator Selection (INTOSC oscillator: I/O function on CLKIN pin)
#pragma config WDTE = OFF       // Watchdog Timer Enable (WDT enabled)
#pragma config PWRTE = OFF      // Power-up Timer Enable (PWRT disabled)
#pragma config MCLRE = OFF      // MCLR Pin Function Select (MCLR/VPP pin function is digital input)
#pragma config CP = OFF         // Flash Program Memory Code Protection (Program memory code protection is disabled)
#pragma config CPD = OFF        // Data Memory Code Protection (Data memory code protection is disabled)
#pragma config BOREN = ON       // Brown-out Reset Enable (Brown-out Reset enabled)
#pragma config CLKOUTEN = OFF   // Clock Out Enable (CLKOUT function is disabled. I/O or oscillator function on the CLKOUT pin)
#pragma config IESO = OFF       // Internal/External Switchover (Internal/External Switchover mode is disabled)
#pragma config FCMEN = ON       // Fail-Safe Clock Monitor Enable (Fail-Safe Clock Monitor is enabled)

// CONFIG2
#pragma config WRT = OFF        // Flash Memory Self-Write Protection (Write protection off)
#pragma config PLLEN = ON       // PLL Enable (4x PLL enabled)
#pragma config STVREN = ON      // Stack Overflow/Underflow Reset Enable (Stack Overflow or Underflow will cause a Reset)
#pragma config BORV = LO        // Brown-out Reset Voltage Selection (Brown-out Reset Voltage (Vbor), low trip point selected.)
#pragma config LVP = ON         // Low-Voltage Programming Enable (Low-voltage programming enabled)

// CPU freq
#define _XTAL_FREQ  (32000000UL)

// LCD const
#define FRAME_LENGTH    12482   // LCD 400x240 : (((400px/8)+2)*240px)+2
#define BYTE_WIDTH      50      // LCD width 400px/8
#define ANIM_DIST       64      // distance of splash animation

// SPI CS pins
#define CS_LCD    RA4

// General purpose
#define LED RA1

//proto
void init();
void interrupt isr();
void clearScreen();
void splashScreen();
unsigned char reverse(unsigned char b);
void i2cHandle();

//global var
unsigned char frameAlt = 0;        // to generate LCD com inversion
unsigned char splashAnimate = 1;   // Splash screen animation
unsigned char vBatt = 0xAA;        // ADC read value

void init(){
    OSCCONbits.IRCF = 0b1110;   // 32MHz
    WDTCONbits.SWDTEN = 0;      // disable watchdog

    ANSELA = 0b00000100;    // analog input on AN2
    ANSELB = 0b00000000;    // no analog input on port b
    ANSELC = 0b00000000;    // no analog input on port C
    TRISA = 0b11111111;
    TRISB = 0b11111111;
    TRISC = 0b11111111;
    
    TRISB7 = 0;             // SPI2 CLK as output
    TRISB5 = 1;             // SPI2 SDI as input
    TRISA5 = 0;             // SPI2 SDO as output
    TRISA4 = 0;             // SPI2 CS_LCD command pin
    TRISA2 = 1;             // RA2 / AN2 as input
    TRISB4 = 1;             // I2C1 SCL as input
    TRISB6 = 1;             // I2C1 SDA as input
    TRISA1 = 0;             // led as output
    
    //SPI conf
    APFCON1bits.SDO2SEL = 1;             // SDO2 function is on RA5
    APFCON1bits.SS2SEL = 1;              // SS2 function is on RA4
    SSP2CON1bits.CKP = 0;                // SPI clk phase
    SSP2STATbits.CKE = 1;                // SPI clk default low
    SSP2CON1bits.SSPM = 0x00;            // SPI clock Fosc/4
    SSP2CON1bits.SSPEN = 1;              // Enable SPI
    
    //ADC conf
    ADCON0bits.CHS = 0b0010; // AN2 selected
    ADCON0bits.ADON = 1;     // adc on
    ADCON1bits.ADFM = 0;     // left justified
    ADCON1bits.ADCS = 0b110; // fosc/64
    ADCON1bits.ADPREF = 0b11;// pos ref = vref
    ADCON1bits.ADNREF = 0b0; // neg ref = gnd
    FVRCONbits.FVREN = 1;    // enable voltage ref
    FVRCONbits.ADFVR = 0b01; // 1.024v ref
    ADCON0bits.GO_nDONE = 1; // start convertion
    
    //I2C conf
    SSP1STATbits.CKE = 1;           // Enable input logic so that thresholds are compliant with SMbus specification
    SSP1ADDbits.SSPADD = 0x08;      // address
    SSP1CON1bits.SSPM = 0b0110;     // I2C slave mode
    SSP1CON1bits.SSPEN = 1;         // Enable I2C
    SSP1CON1bits.CKP = 1;           // Enable clock
    SSP1CON2bits.SEN = 1;           // clock streching
    SSP1CON3bits.AHEN = 0;          // Address holding
    SSP1CON3bits.DHEN = 0;          // Data holding
    SSP1CON3bits.BOEN = 1;          // ignoring the state of the SSPOV
    
    //interrupts
    INTCONbits.PEIE = 1;
    INTCONbits.GIE = 1;
    PIE1bits.SSP1IE = 1;    // Enable interrupt for I2C1
    PIE4bits.SSP2IE = 0;    // Disable interrupt for SPI2    
    
    CS_LCD = 0;
    
    __delay_ms(1);
}

// interrupt
void interrupt isr() {
    LED = !LED;
    
    if (INTCONbits.INTF){ // woke-up from interrupt
        INTCONbits.INTF = 0;
    }
    if (PIR1bits.SSP1IF) { // I2C interrupt
        i2cHandle();
    }
}

// Our address is recieved on I2C
void i2cHandle(){
    if (splashAnimate == 1) {   // diable SPI2 & high Z
        splashAnimate = 0;
        SSP2CON1bits.SSPEN = 0; // Disable SPI
        TRISB7 = 1;             // SPI2 CLK as input
        TRISB5 = 1;             // SPI2 SDI as input
        TRISA5 = 1;             // SPI2 SDO as input
        TRISA4 = 1;             // SPI2 CS_LCD input
    }
    
    ADCON0bits.GO_nDONE = 1;    // relaunch convertion
    while(ADCON0bits.GO_nDONE){;}
    vBatt = ADRESH;
    
    unsigned char ssp_Buf;
    unsigned char i2c_byte_count = 0;
    
    if (SSP1STATbits.BF) { // Discard slave address 
            ssp_Buf = SSP1BUF; // Clear BF
    }
    
    SSP1CON1bits.WCOL = 0;
    
    if (!SSP1STATbits.D_nA) { // Slave Address 
            
        i2c_byte_count = 0;

        if (SSP1STATbits.R_nW) { // Reading 
            SSP1BUF = ssp_Buf;
        } 

    } else { // Data bytes 

        i2c_byte_count++;

        if (SSP1STATbits.R_nW) { // Multi-byte read
            SSP1BUF = ssp_Buf;
        } 
    }

    // Finally
    PIR1bits.SSP1IF = 0; // Clear MSSP interrupt flag
    SSP1CON1bits.CKP = 1; // Release clock 
    
}

void clearScreen(){
    CS_LCD = 1;
    SSP2BUF = 0x20;
    while (SSP2STATbits.BF == 0){;}
    SSP2BUF = 0x00;
    while (SSP2STATbits.BF == 0){;}
    CS_LCD = 0;
}

void splashScreen(){
    unsigned char i = 0;
    unsigned char j = 0;
    
    CS_LCD = 1;
    
    // PolaPi logo
    for (j=0; j<logoHeight; j++) {
        if (j == 0) {
            if (frameAlt%2) SSP2BUF = 0xC0;
            else SSP2BUF = 0x80;
        } else {
            SSP2BUF = 0x00; // dummy byte
        }
        while (SSP2STATbits.BF == 0){;}
        SSP2BUF = reverse(95+j);     // address
        while (SSP2STATbits.BF == 0){;}
        for(i=0; i<5; i++) {
            SSP2BUF = 0xFF;
            while (SSP2STATbits.BF == 0){;}
        }
        for(i=0; i<logoWidth; i++) {
            if ((i+(j>>3))%ANIM_DIST == frameAlt%ANIM_DIST) {
                if (j%2 == 0) SSP2BUF = logo[i+(j*logoWidth)] | 0x24;
                else SSP2BUF = logo[i+(j*logoWidth)] | 0x42;
            } else if ((i+1+(j>>3))%ANIM_DIST == frameAlt%ANIM_DIST) {
                if (j%2 == 0) SSP2BUF = logo[i+(j*logoWidth)] | 0xAA;
                else SSP2BUF = logo[i+(j*logoWidth)] | 0x55;
            } else if ((i+2+(j>>3))%ANIM_DIST == frameAlt%ANIM_DIST){
                if (j%2 == 0) SSP2BUF = logo[i+(j*logoWidth)] | 0x77;
                else SSP2BUF = logo[i+(j*logoWidth)] | 0xEE;
            } else if ((i+3+(j>>3))%ANIM_DIST == frameAlt%ANIM_DIST) {
                if (j%2 == 0) SSP2BUF = logo[i+(j*logoWidth)] | 0xAA;
                else SSP2BUF = logo[i+(j*logoWidth)] | 0x55;
            } else if ((i+4+(j>>3))%ANIM_DIST == frameAlt%ANIM_DIST){
                if (j%2 == 0) SSP2BUF = logo[i+(j*logoWidth)] | 0x24;
                else SSP2BUF = logo[i+(j*logoWidth)] | 0x42;
            } else SSP2BUF = logo[i+(j*logoWidth)];
            while (SSP2STATbits.BF == 0){;}
        }
        for(i=0; i<5; i++) {
            SSP2BUF = 0xFF;
            while (SSP2STATbits.BF == 0){;}
        }
    }
    
    // end of frame
    SSP2BUF = 0x00; // dummy byte
    while (SSP2STATbits.BF == 0){;}
    SSP2BUF = 0x00; // dummy byte
    while (SSP2STATbits.BF == 0){;}
    
    CS_LCD = 0;
    frameAlt++;
}

unsigned char reverse(unsigned char b) {
   b = (b & 0xF0) >> 4 | (b & 0x0F) << 4;
   b = (b & 0xCC) >> 2 | (b & 0x33) << 2;
   b = (b & 0xAA) >> 1 | (b & 0x55) << 1;
   return b;
}

void main(void) {
    init();
    clearScreen();
    
    while(1){
        
        if(splashAnimate) splashScreen();
        
        __delay_ms(1);
    }
    return;
}
