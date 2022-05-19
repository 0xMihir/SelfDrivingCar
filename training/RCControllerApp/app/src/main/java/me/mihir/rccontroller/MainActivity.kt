package me.mihir.rccontroller

import android.Manifest
import android.annotation.SuppressLint
import android.bluetooth.BluetoothAdapter
import android.bluetooth.BluetoothDevice
import android.bluetooth.BluetoothManager
import android.bluetooth.BluetoothSocket
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Bundle
import android.os.HandlerThread
import android.os.Looper
import android.util.Log
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.interaction.collectIsPressedAsState
import androidx.compose.foundation.layout.*
import androidx.compose.material.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.TransformOrigin
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.layout.layout
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.Constraints
import androidx.compose.ui.unit.dp
import androidx.core.app.ActivityCompat
import androidx.core.view.ViewCompat
import androidx.core.view.WindowInsetsCompat
import androidx.core.view.WindowInsetsControllerCompat
import me.mihir.rccontroller.ui.theme.RCControllerTheme
import java.io.IOException
import java.util.*
import kotlin.math.roundToInt

class MainActivity : ComponentActivity() {
    private val REQUEST_ENABLE_BT_SCAN = 101
    private val STEER: Byte = 0
    private val THROTTLE: Byte = 1
    private val LEFT: Byte = 1
    private val CENTER: Byte = 0
    private val RIGHT: Byte = 2
    private lateinit var bluetoothAdapter: BluetoothAdapter

    private lateinit var msgHandler: MessageHandler
    override fun onCreate(savedInstanceState: Bundle?) {
        val bluetoothManager: BluetoothManager = getSystemService(BluetoothManager::class.java)
        bluetoothAdapter = bluetoothManager.adapter
        if (!bluetoothAdapter.isEnabled) {
            val enableBtIntent = Intent(BluetoothAdapter.ACTION_REQUEST_ENABLE)
            if (ActivityCompat.checkSelfPermission(
                    this,
                    Manifest.permission.BLUETOOTH_SCAN
                ) != PackageManager.PERMISSION_GRANTED
                || ActivityCompat.checkSelfPermission(
                    this,
                    Manifest.permission.BLUETOOTH_CONNECT
                ) != PackageManager.PERMISSION_GRANTED
            ) {
                requestPermissions(
                    arrayOf(
                        Manifest.permission.BLUETOOTH_SCAN,
                        Manifest.permission.BLUETOOTH_CONNECT
                    ),
                    REQUEST_ENABLE_BT_SCAN
                )
            }
            resultLauncher.launch(enableBtIntent)

        }

        val windowInsetsController =
            ViewCompat.getWindowInsetsController(window.decorView) ?: return

        windowInsetsController.systemBarsBehavior =
            WindowInsetsControllerCompat.BEHAVIOR_SHOW_TRANSIENT_BARS_BY_SWIPE
        windowInsetsController.hide(WindowInsetsCompat.Type.systemBars())

        super.onCreate(savedInstanceState)
        val pairedDevices: Set<BluetoothDevice>? = bluetoothAdapter.bondedDevices
        // Note: Hardcoded
        val device = pairedDevices?.find { device -> device.name == "raspberrypi" }
        if (device != null) ConnectThread(device).start()
        setContent {
            RCControllerTheme {
                // A surface container using the 'background' color from the theme
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = MaterialTheme.colors.background
                ) {
                    Row(
                        modifier = Modifier
                            .height(IntrinsicSize.Max)
                            .width(IntrinsicSize.Max)
                            .padding(64.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        SteeringButton(onPress = {
                            if (::msgHandler.isInitialized) {
                                val pressMsg = msgHandler.obtainMessage()
                                pressMsg.obj = byteArrayOf(STEER, LEFT)
                                msgHandler.sendMessage(pressMsg)
                            }
                        }, onRelease = {
                            if (::msgHandler.isInitialized) {
                                val releaseMsg = msgHandler.obtainMessage()
                                releaseMsg.obj = byteArrayOf(STEER, CENTER)
                                msgHandler.sendMessage(releaseMsg)
                            }
                        }, text = "Left")

                        Spacer(Modifier.width(32.dp))

                        SteeringButton(onPress = {
                            if (::msgHandler.isInitialized) {
                                val pressMsg = msgHandler.obtainMessage()
                                pressMsg.obj = byteArrayOf(STEER, RIGHT)
                                msgHandler.sendMessage(pressMsg)
                            }
                        }, onRelease = {
                            if (::msgHandler.isInitialized) {
                                val releaseMsg = msgHandler.obtainMessage()
                                releaseMsg.obj = byteArrayOf(STEER, CENTER)
                                msgHandler.sendMessage(releaseMsg)
                            }
                        }, text = "Right")

                        Spacer(Modifier.weight(1f))


                        Row(Modifier.height(300.dp)) {
                            Throttle {
                                if (::msgHandler.isInitialized) {
                                    val msg = msgHandler.obtainMessage()
                                    msg.obj = byteArrayOf(
                                        THROTTLE,
                                        (it * 127).roundToInt().toByte()
                                    )
                                    msgHandler.sendMessage(msg)
                                }
                            }
                        }

                        Spacer(Modifier.width(140.dp))
                    }
                }
            }
        }


    }

    @SuppressLint("MissingPermission")
    private inner class ConnectThread(device: BluetoothDevice) : Thread() {

        private val bluetoothSocket: BluetoothSocket? by lazy(LazyThreadSafetyMode.NONE) {
            if (ActivityCompat.checkSelfPermission(
                    this@MainActivity,
                    Manifest.permission.BLUETOOTH_CONNECT
                ) == PackageManager.PERMISSION_GRANTED
            ) {
                device.createRfcommSocketToServiceRecord(
                    UUID.fromString("534cb228-39b8-4009-9327-27dca1e528cf")
                )
            } else {
                null
            }
        }

        override fun run() {
            Looper.prepare()

            if (ActivityCompat.checkSelfPermission(
                    this@MainActivity,
                    Manifest.permission.BLUETOOTH_SCAN
                ) == PackageManager.PERMISSION_GRANTED
            ) {
                bluetoothAdapter.cancelDiscovery()

                bluetoothSocket?.let { socket ->

                    try {
                        socket.connect()
                    } catch (err: IOException) {
                        Toast.makeText(
                            this@MainActivity,
                            "Connection failed, Check Pi!",
                            Toast.LENGTH_LONG
                        ).show()
                        this.cancel()
                        return
                    }
                    Log.d("Socket", "Connected!")

                    val msgThread = HandlerThread("MessageThread")
                    msgThread.start()
                    msgHandler = MessageHandler(msgThread.looper, socket)

                }
            }

        }

        // Closes the client socket and causes the thread to finish.
        fun cancel() {
            try {
                bluetoothSocket?.close()
            } catch (e: IOException) {
                Log.e("ConnectThread", "Could not close the client socket", e)
            }
        }
    }

    private val resultLauncher =
        registerForActivityResult(ActivityResultContracts.StartActivityForResult()) {}
}

@Composable
fun SteeringButton(onPress: () -> Unit, onRelease: () -> Unit, text: String) {
    val interactionSource = remember { MutableInteractionSource() }
    val pressed by interactionSource.collectIsPressedAsState()

    if (pressed) {
        onPress()
        DisposableEffect(Unit) {
            onDispose {
                onRelease()
            }
        }
    }

    Button(
        modifier = Modifier
            .height(100.dp)
            .aspectRatio(1f),
        interactionSource = interactionSource,
        onClick = { }) {
        Text(text)
    }
}

@Composable
fun Throttle(onChange: (Float) -> Unit) {
    var sliderPosition by remember { mutableStateOf(.5f) }

    Slider(sliderPosition, {
        sliderPosition = it
        val throttle = (it - 0.5f) * 2
        onChange(throttle)
    }, onValueChangeFinished = {
        sliderPosition = 0.5f
        onChange(0f)
    }, modifier = Modifier
        .graphicsLayer {
            rotationZ = 270f
            transformOrigin = TransformOrigin(0f, 0f)
        }
        .layout { measurable, constraints ->
            val placeable = measurable.measure(
                Constraints(
                    minWidth = constraints.minHeight,
                    maxWidth = constraints.maxHeight,
                    minHeight = constraints.minWidth,
                    maxHeight = constraints.maxWidth,
                )
            )
            layout(placeable.height, placeable.width) {
                placeable.place(-placeable.width, 0)
            }
        }
        .width(300.dp)
        .height(50.dp))
}


@Preview(showBackground = true)
@Composable
fun DefaultPreview() {
    RCControllerTheme {
        Throttle {}
    }
}