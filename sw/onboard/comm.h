#ifndef COMM_H
#define COMM_H

//#include "std.h"
#include "generated/messages.h"

typedef enum {
    COMM_1,
    COMM_2,
    COMM_NB
} CommChannel_t;

typedef enum {
    STATE_UNINIT,
    STATE_GOT_STX,
    STATE_GOT_LENGTH,
    STATE_GOT_ACID,
    STATE_GOT_MSGID,
    STATE_GOT_PAYLOAD,
    STATE_GOT_CRC1
} ParseState_t; ///< The state machine for the comm parser
    
typedef struct __CommStatus {
    uint8_t ck_a; ///< Checksum byte 1
    uint8_t ck_b; ///< Checksum byte 2
    uint8_t msg_received;
    uint8_t buffer_overrun; ///< Number of buffer overruns
    uint8_t parse_error; ///< Number of parse errors
    ParseState_t parse_state; ///< Parsing state machine
} CommStatus_t;

typedef uint8_t (*CommRXMessageCallback_t)(CommChannel_t chan, CommMessage_t *message);
typedef uint8_t (*CommTXMessageCallback_t)(CommChannel_t chan, uint8_t msgid);

///< @todo What is the result of using extern here? Why not static?
extern CommRXMessageCallback_t  comm_callback_rx[COMM_NB];
extern CommTXMessageCallback_t  comm_callback_tx[COMM_NB];
extern CommMessage_t            comm_message[COMM_NB];
extern CommStatus_t             comm_status[COMM_NB];
extern uint8_t                  comm_channel_used[COMM_NB];

/**
 * @brief Initialize the communication channel
 */
void comm_init ( CommChannel_t chan );

void
comm_add_rx_callback ( CommChannel_t chan, CommRXMessageCallback_t cb);

void
comm_add_tx_callback ( CommChannel_t chan, CommTXMessageCallback_t cb);

void
comm_periodic_task ( CommChannel_t chan );

uint8_t
comm_event_task ( CommChannel_t chan );

uint8_t
comm_ch_available ( CommChannel_t chan );

void
comm_send_message_ch ( CommChannel_t chan, uint8_t c );

/**
 * @brief Send one char over the comm channel
 *
 * This stub has to be implemented by each individual platform
 *
 * @param chan the comm channel
 * @param c char to send
 */
void comm_send_ch ( CommChannel_t chan, uint8_t c );

/**
 * @brief Send a whole message over a the comm channel
 *
 * This stub has to be implemented by each individual platform
 *
 * @param chan the comm channel
 * @param message the message to send
 */
void comm_send_message ( CommChannel_t chan, CommMessage_t* message );

/**
 * @brief Send comm status message
 * 
 * As the comm subsystem holds it's status internally, it can send
 * status messages just by the correct id. It returns 0 if the ID could
 * not be found and the status message has not been send.
 *
 * @param chan the comm channel to use
 * @param msgid message id of the status message to send
 * @return 0 if message id could not be found or error occured, 1 on success
 */
uint8_t comm_send_message_by_id (CommChannel_t chan, uint8_t msgid);

/**
 * @brief Get one char from the comm channel
 *
 * This stub has to be implemented by each individual platform
 *
 * @param chan The channel to get one char from
 * @return The next char
 */
uint8_t comm_get_ch( CommChannel_t chan );

/**
 * @brief Check free space to send on a channel
 *
 * This stub has to be implemented by each individual platform
 *
 * @param chan The channel write to
 * @return 1 if space is available, 0 else
 */
uint8_t comm_check_free_space ( CommChannel_t chan, uint8_t len );

void comm_start_message( CommChannel_t chan, uint8_t id, uint8_t len );

void
comm_end_message ( CommChannel_t chan );

///< @todo not totally clear what the parsing output is.
uint8_t comm_parse(CommChannel_t chan);

void
comm_overrun ( CommChannel_t chan );

#endif /* COMM_H */

