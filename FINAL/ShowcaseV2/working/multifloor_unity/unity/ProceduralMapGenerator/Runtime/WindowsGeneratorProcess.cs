using System;
using System.ComponentModel;
using System.Runtime.InteropServices;
using System.Text;

namespace ProceduralMapGenerator
{
    // Unity's Windows IL2CPP player cannot reliably launch the worker through Process.Start.
    internal sealed class WindowsGeneratorProcess : IDisposable
    {
        private IntPtr handle;

        public WindowsGeneratorProcess(string executable, string arguments, string directory)
        {
            if (!RuntimeInformation.IsOSPlatform(OSPlatform.Windows))
                throw new PlatformNotSupportedException("Map generation is supported on Windows.");

            var startup = new StartupInfo { size = Marshal.SizeOf<StartupInfo>() };
            var command = new StringBuilder($"\"{executable}\" {arguments}");
            const uint createNoWindow = 0x08000000;
            if (!CreateProcessW(executable, command, IntPtr.Zero, IntPtr.Zero, false,
                createNoWindow, IntPtr.Zero, directory, ref startup, out ProcessInfo info))
                throw new Win32Exception(Marshal.GetLastWin32Error());

            CloseHandle(info.thread);
            handle = info.process;
        }

        public bool HasExited
        {
            get
            {
                uint result = WaitForSingleObject(handle, 0);
                if (result == uint.MaxValue)
                    throw new Win32Exception(Marshal.GetLastWin32Error());
                return result == 0;
            }
        }

        public uint ExitCode
        {
            get
            {
                if (!GetExitCodeProcess(handle, out uint code))
                    throw new Win32Exception(Marshal.GetLastWin32Error());
                return code;
            }
        }

        public void Dispose()
        {
            if (handle == IntPtr.Zero)
                return;
            if (WaitForSingleObject(handle, 0) == 258)
                TerminateProcess(handle, 1);
            CloseHandle(handle);
            handle = IntPtr.Zero;
        }

        [StructLayout(LayoutKind.Sequential)]
        private struct StartupInfo
        {
            public int size;
            public IntPtr reserved, desktop, title;
            public uint x, y, width, height, xChars, yChars, fill, flags;
            public ushort show, reservedSize;
            public IntPtr reservedBytes, stdin, stdout, stderr;
        }

        [StructLayout(LayoutKind.Sequential)]
        private struct ProcessInfo
        {
            public IntPtr process, thread;
            public uint processId, threadId;
        }

        [DllImport("kernel32.dll", CharSet = CharSet.Unicode, ExactSpelling = true, SetLastError = true)]
        private static extern bool CreateProcessW(string application, StringBuilder command,
            IntPtr processAttributes, IntPtr threadAttributes, bool inheritHandles, uint flags,
            IntPtr environment, string directory, ref StartupInfo startup, out ProcessInfo result);

        [DllImport("kernel32.dll", SetLastError = true)]
        private static extern bool CloseHandle(IntPtr handle);

        [DllImport("kernel32.dll", SetLastError = true)]
        private static extern uint WaitForSingleObject(IntPtr handle, uint milliseconds);

        [DllImport("kernel32.dll", SetLastError = true)]
        private static extern bool GetExitCodeProcess(IntPtr handle, out uint code);

        [DllImport("kernel32.dll", SetLastError = true)]
        private static extern bool TerminateProcess(IntPtr handle, uint code);
    }
}
