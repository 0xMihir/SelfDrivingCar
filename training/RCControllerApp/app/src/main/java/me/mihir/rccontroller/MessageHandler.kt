package me.mihir.rccontroller

import android.bluetooth.BluetoothSocket
import android.os.*
import android.util.Log
import java.io.IOException
class MessageHandler(looper: Looper, socket: BluetoothSocket) : Handler(looper) {
    private val TAG = "MessageHandler"
    private var socketOpen = true;
    private val mSocket = socket
    fun ByteArray.toHex(): String =
        joinToString(separator = "") { eachByte -> "%02x".format(eachByte) }

    public override fun handleMessage(msg: Message) {
        if (socketOpen) {
            try {
                mSocket.outputStream.write(msg.obj as ByteArray)
            } catch (err: IOException) {
                if (err.message == "Broken Pipe") {
                    Log.e(TAG, "Socket Closed")
                    socketOpen = false
                    mSocket.close()
                    looper.quitSafely()
                    this.removeCallbacksAndMessages(null);
                }
            }
        }
        super.handleMessage(msg)
    }

}