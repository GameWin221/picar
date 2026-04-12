#include "debug.h"

#define SDA_PIN GPIO_Pin_1
#define SCL_PIN GPIO_Pin_2

#define SERVO_CH1_PIN GPIO_Pin_6
#define SERVO_CH2_PIN GPIO_Pin_7
#define SERVO_CH3_PIN GPIO_Pin_3
#define SERVO_CH4_PIN GPIO_Pin_4
#define SERVO_PIN_TYPE GPIOC
#define SERVO_TIMER TIM1

#define MOT_DIRF_PIN GPIO_Pin_4
#define MOT_DIRB_PIN GPIO_Pin_0
#define MOT_DIRF_PIN_TYPE GPIOD
#define MOT_DIRB_PIN_TYPE GPIOC

#define MOT_PWML_PIN GPIO_Pin_5
#define MOT_PWMR_PIN GPIO_Pin_6
#define MOT_PWM_PIN_TYPE GPIOD
#define MOTOR_TIMER TIM2

#define BAT_VOLTAGE_PIN GPIO_Pin_1
#define BAT_VOLTAGE_PIN_TYPE GPIOA

#define LED_PIN GPIO_Pin_2
#define LED_PIN_TYPE GPIOA

#define PWM_PERIOD 1000

#define I2C_RX_ADDR (0x17<<1) // the real address is still 0x17 because of internal shifting - i.e. master still sends to slave on 0x17

void IIC_Init(u32 baudrate, u16 address){
    RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOC, ENABLE);
    
    RCC_APB2PeriphClockCmd(RCC_APB2Periph_AFIO, ENABLE);
    RCC_APB1PeriphResetCmd(RCC_APB1Periph_I2C1, ENABLE);
    RCC_APB1PeriphResetCmd(RCC_APB1Periph_I2C1, DISABLE);
    RCC_APB1PeriphClockCmd(RCC_APB1Periph_I2C1, ENABLE);
    
    GPIO_InitTypeDef GPIO_InitStructure={0};
    GPIO_InitStructure.GPIO_Pin = SDA_PIN | SCL_PIN;
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_AF_OD;
    GPIO_InitStructure.GPIO_Speed = GPIO_Speed_30MHz;
    GPIO_Init(GPIOC, &GPIO_InitStructure);

    I2C_InitTypeDef I2C_InitTSturcture={0};
    I2C_InitTSturcture.I2C_ClockSpeed = baudrate;
    I2C_InitTSturcture.I2C_Mode = I2C_Mode_I2C;
    I2C_InitTSturcture.I2C_DutyCycle = I2C_DutyCycle_16_9;
    I2C_InitTSturcture.I2C_OwnAddress1 = address;
    I2C_InitTSturcture.I2C_Ack = I2C_Ack_Enable;
    I2C_InitTSturcture.I2C_AcknowledgedAddress = I2C_AcknowledgedAddress_7bit;
    I2C_Init(I2C1, &I2C_InitTSturcture);

    I2C_Cmd(I2C1, ENABLE);
}

void PWM_Init() {
    RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOD | RCC_APB2Periph_GPIOC | RCC_APB2Periph_TIM1 | RCC_APB2Periph_AFIO, ENABLE);
    RCC_APB1PeriphClockCmd(RCC_APB1Periph_TIM2, ENABLE);
    
    GPIO_PinRemapConfig(GPIO_PartialRemap1_TIM1, ENABLE);
    GPIO_PinRemapConfig(GPIO_FullRemap_TIM2, ENABLE);

    GPIO_InitTypeDef GPIO_InitStructure = {0};
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_AF_PP;
    GPIO_InitStructure.GPIO_Speed = GPIO_Speed_30MHz;
    GPIO_InitStructure.GPIO_Pin = SERVO_CH1_PIN | SERVO_CH2_PIN | SERVO_CH3_PIN | SERVO_CH4_PIN;
    GPIO_Init(SERVO_PIN_TYPE, &GPIO_InitStructure);

    // Motor PWM pins: PD5 (MOT_PWML), PD6 (MOT_PWMR)
    GPIO_InitStructure.GPIO_Pin = MOT_PWML_PIN | MOT_PWMR_PIN;
    GPIO_Init(MOT_PWM_PIN_TYPE, &GPIO_InitStructure);

    TIM_TimeBaseInitTypeDef TIM_TimeBaseInitStructure={0};
    TIM_TimeBaseInitStructure.TIM_Period = PWM_PERIOD;
    TIM_TimeBaseInitStructure.TIM_Prescaler = 0;
    TIM_TimeBaseInitStructure.TIM_ClockDivision = TIM_CKD_DIV1;
    TIM_TimeBaseInitStructure.TIM_CounterMode = TIM_CounterMode_Up;
    TIM_TimeBaseInit(SERVO_TIMER, &TIM_TimeBaseInitStructure);
    TIM_TimeBaseInit(MOTOR_TIMER, &TIM_TimeBaseInitStructure);

    TIM_OCInitTypeDef TIM_OCInitStructure={0};
    TIM_OCInitStructure.TIM_OCMode = TIM_OCMode_PWM1; // Edge aligned
    TIM_OCInitStructure.TIM_OutputState = TIM_OutputState_Enable;
    TIM_OCInitStructure.TIM_Pulse = 0; // Start with 0% duty cycle
    TIM_OCInitStructure.TIM_OCPolarity = TIM_OCPolarity_High;

    TIM_OC1Init(SERVO_TIMER, &TIM_OCInitStructure);
    TIM_OC2Init(SERVO_TIMER, &TIM_OCInitStructure);
    TIM_OC3Init(SERVO_TIMER, &TIM_OCInitStructure);
    TIM_OC4Init(SERVO_TIMER, &TIM_OCInitStructure);

    TIM_OC1PreloadConfig(SERVO_TIMER, TIM_OCPreload_Enable);
    TIM_OC2PreloadConfig(SERVO_TIMER, TIM_OCPreload_Enable);
    TIM_OC3PreloadConfig(SERVO_TIMER, TIM_OCPreload_Enable);
    TIM_OC4PreloadConfig(SERVO_TIMER, TIM_OCPreload_Enable);

    TIM_OC3Init(MOTOR_TIMER, &TIM_OCInitStructure);  // PD6 (MOT_PWMR) - TIM2_CH3
    TIM_OC4Init(MOTOR_TIMER, &TIM_OCInitStructure);  // PD5 (MOT_PWML) - TIM2_CH4

    TIM_OC3PreloadConfig(MOTOR_TIMER, TIM_OCPreload_Enable);
    TIM_OC4PreloadConfig(MOTOR_TIMER, TIM_OCPreload_Enable);

    TIM_ARRPreloadConfig(SERVO_TIMER, ENABLE);
    TIM_ARRPreloadConfig(MOTOR_TIMER, ENABLE);
    TIM_CtrlPWMOutputs(SERVO_TIMER, ENABLE);
    //TIM_CtrlPWMOutputs(TIM2, ENABLE); // Not needed for TIM2
    TIM_Cmd(SERVO_TIMER, ENABLE);
    TIM_Cmd(MOTOR_TIMER, ENABLE);
}

void MOT_DIR_Init() {
    // Enable clocks for GPIOD and GPIOC
    RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOD | RCC_APB2Periph_GPIOC, ENABLE);
    
    // Initialize MOT_DIRF_PIN (PD4) as GPIO output
    GPIO_InitTypeDef GPIO_InitStructure = {0};
    GPIO_InitStructure.GPIO_Pin = MOT_DIRF_PIN;
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_Out_PP;  // Push-pull output
    GPIO_InitStructure.GPIO_Speed = GPIO_Speed_30MHz;
    GPIO_Init(MOT_DIRF_PIN_TYPE, &GPIO_InitStructure);
    
    // Initialize MOT_DIRB_PIN (PC0) as GPIO output
    GPIO_InitStructure.GPIO_Pin = MOT_DIRB_PIN;
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_Out_PP;  // Push-pull output
    GPIO_InitStructure.GPIO_Speed = GPIO_Speed_30MHz;
    GPIO_Init(MOT_DIRB_PIN_TYPE, &GPIO_InitStructure);
    
    // Set initial direction (both LOW)
    GPIO_WriteBit(MOT_DIRF_PIN_TYPE, MOT_DIRF_PIN, Bit_RESET);
    GPIO_WriteBit(MOT_DIRB_PIN_TYPE, MOT_DIRB_PIN, Bit_RESET);
}

void PWM_SetDuty(TIM_TypeDef *timer, uint8_t channel, uint16_t duty_cycle) {
    if (duty_cycle > PWM_PERIOD) {
        duty_cycle = PWM_PERIOD;
    }

    switch (channel) {
        case 1:
            TIM_SetCompare1(timer, duty_cycle);
            break;
        case 2:
            TIM_SetCompare2(timer, duty_cycle);
            break;
        case 3:
            TIM_SetCompare3(timer, duty_cycle);
            break;
        case 4:
            TIM_SetCompare4(timer, duty_cycle);
            break;
    }
}

void PWM_SetFreq(TIM_TypeDef *timer, uint16_t frequency) {
    // Since SystemCoreClock is usually no more than 48MHz and PWM_PERIOD is equal to 1000, 
    // the max effective PWM frequency is 48000Hz. Trying to set the frequency to anything 
    // greater than this value will cap the value to 48000Hz.
    uint32_t prescaler = SystemCoreClock / (PWM_PERIOD * frequency);
    if(prescaler == 0) {
        prescaler = 1;
    }

    // According to the reference manual section 10.2.3 Counters and peripherals: 
    // "[...] the PSC is 16-bit and the actual dividing factor is equal to the value of R16_TIMx_PSC + 1."
    timer->PSC = (uint16_t)(prescaler-1);
    timer->SWEVGR = TIM_PSCReloadMode_Immediate;
}

int main(void) {
    NVIC_PriorityGroupConfig(NVIC_PriorityGroup_1);
    SystemCoreClockUpdate();
    Delay_Init();

    Delay_Ms(5);

    // Init pins
    MOT_DIR_Init();
    PWM_Init();

    // Init defaults for PWM timers
    PWM_SetFreq(SERVO_TIMER, 50);
    PWM_SetFreq(MOTOR_TIMER, 10000);

    IIC_Init(100000, I2C_RX_ADDR);
    I2C1->CTLR1 |= 0x0080; // CTLR1_NOSTRETCH_Set - Disable clock stretching
    I2C1->CTLR1 |= 0x0400; // CTLR1_ACK_Set - Enable ACK following each byte received - This also stops the clock stretching for each character received.
    // Thanks to Jim Merkle's code for those two lines above ^^: https://github.com/JimMerkle/CH32V003_I2C_Slave/blob/master/User/main.c
    // TODO: Try to get rid of those lines because they theoretically shouldn't be necassary but they are needed for I2C to work properly on my board. 

    uint8_t i2c_is_register_ok = 0;
    uint8_t i2c_bytes_read = 0;
    uint8_t i2c_register = 0;
    uint16_t i2c_data = 0;

    volatile uint16_t temp;
    (void)temp;

    while (1) {
        while(!I2C_CheckEvent(I2C1, I2C_EVENT_SLAVE_RECEIVER_ADDRESS_MATCHED));
    
        // Clear ADDR by reading the regs
        temp = I2C1->STAR1;
        temp = I2C1->STAR2;

        // TODO: add support for reading registers

        // Receive byte until STOP
        while (I2C_GetFlagStatus(I2C1, I2C_FLAG_STOPF) == RESET) {
            if (I2C_GetFlagStatus(I2C1, I2C_FLAG_RXNE) != RESET) {
                uint8_t data = I2C_ReceiveData(I2C1);
                
                if (!i2c_is_register_ok) {
                    i2c_register = data;
                    i2c_is_register_ok = 1;
                } else {
                    i2c_data |= (uint16_t)(data << (i2c_bytes_read * 8));
                    i2c_bytes_read += 1;
                }
            }
        }

        // Clear STOPF flag
        temp = I2C1->STAR1;
        I2C1->CTLR1 |= 0x0001;

        // Finish transfer and process the data (temporary solution for as long as there are no readable registers)
        if(i2c_bytes_read >= 2 && i2c_is_register_ok) {
            /// Available registers 
            // ID (DEC) | Access     | Data type | Description                           | Valid values
            // 1        | write-only | uint16_t  | TIM1 frequency                        | [1; 48000]
            // 2        | write-only | uint16_t  | TIM2 frequency                        | [1; 48000]
    
            // 4        | write-only | uint16_t  | TIM1 CH1 duty cycle (Servo CH1 PWM)   | [0; PWM_PERIOD)
            // 5        | write-only | uint16_t  | TIM1 CH2 duty cycle (Servo CH2 PWM)   | [0; PWM_PERIOD)
            // 6        | write-only | uint16_t  | TIM1 CH3 duty cycle (Servo CH3 PWM)   | [0; PWM_PERIOD)
            // 7        | write-only | uint16_t  | TIM1 CH4 duty cycle (Servo CH4 PWM)   | [0; PWM_PERIOD)

            // 10       | write-only | uint16_t  | TIM2 CH3 duty cycle (Right Motor PWM) | [0; PWM_PERIOD)
            // 11       | write-only | uint16_t  | TIM2 CH4 duty cycle (Left Motor PWM)  | [0; PWM_PERIOD)

            // 12       | write-only | uint16_t  | Motor direction: (DIRF | (DIRB << 8)) | {0, 1, (1 << 8), 1 | (1 << 8) }

            switch (i2c_register) {
                case 1: 
                    PWM_SetFreq(TIM1, i2c_data);
                    break;

                case 2: 
                    PWM_SetFreq(TIM2, i2c_data);
                    break;

                case 4: 
                case 5: 
                case 6:
                case 7: 
                    PWM_SetDuty(TIM1, i2c_register - 4 + 1, i2c_data);
                    break;

                case 10: 
                case 11: 
                    PWM_SetDuty(TIM2, i2c_register - 8 + 1, i2c_data);
                    break;

                case 12: 
                    GPIO_WriteBit(MOT_DIRF_PIN_TYPE, MOT_DIRF_PIN, i2c_data & 1);
                    GPIO_WriteBit(MOT_DIRB_PIN_TYPE, MOT_DIRB_PIN, (i2c_data >> 8) & 1);
                    break;

                default: 
                    // do nothing
                    break;
            }

            // Return to the default state
            i2c_is_register_ok = 0;
            i2c_bytes_read = 0;
            i2c_register = 0;
            i2c_data = 0;
        }
    }
}
