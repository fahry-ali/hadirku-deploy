document.addEventListener('DOMContentLoaded', function() {
    const video = document.getElementById('video');
    const canvas = document.getElementById('canvas');
    const attendBtn = document.getElementById('attend-btn');
    const context = canvas.getContext('2d');

    // Mengakses webcam pengguna
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        navigator.mediaDevices.getUserMedia({ video: true })
            .then(function(stream) {
                video.srcObject = stream;
                video.play();
            })
            .catch(function(error) {
                console.error("Error accessing camera: ", error);
                Swal.fire('Error', 'Tidak dapat mengakses kamera. Pastikan Anda memberikan izin.', 'error');
            });
    }

    // Event listener untuk tombol presensi
    attendBtn.addEventListener('click', function() {
        const courseSelect = document.getElementById('course-select');
        const selectedCourseId = courseSelect.value;

        // Validasi apakah mata kuliah sudah dipilih
        if (!selectedCourseId || courseSelect.selectedIndex === 0) {
            Swal.fire('Peringatan', 'Anda harus memilih mata kuliah terlebih dahulu.', 'warning');
            return;
        }

        // Tampilkan loading spinner
        Swal.fire({
            title: 'Memproses...',
            text: 'Mohon tunggu, sedang mengambil lokasi dan mengenali wajah Anda.',
            allowOutsideClick: false,
            didOpen: () => {
                Swal.showLoading();
            }
        });

        // 1. Dapatkan lokasi geografis
        navigator.geolocation.getCurrentPosition(
            (position) => {
                const location = {
                    latitude: position.coords.latitude,
                    longitude: position.coords.longitude
                };

                // 2. Ambil gambar dari video
                context.drawImage(video, 0, 0, canvas.width, canvas.height);
                const imageData = canvas.toDataURL('image/jpeg');

                // 3. Kirim data ke server
                fetch('/mark_attendance', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            image_data: imageData,
                            location: location,
                            matakuliah_id: selectedCourseId // Kirim ID mata kuliah
                        }),
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.status === 'success') {
                            Swal.fire('Berhasil!', data.message, 'success')
                                .then(() => {
                                    // Redirect ke halaman riwayat setelah presensi berhasil
                                    window.location.href = '/records';
                                });
                        } else if (data.status === 'warning') {
                            Swal.fire('Info', data.message, 'info');
                        } else { // status === 'error'
                            Swal.fire('Gagal!', data.message, 'error');
                        }
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        Swal.fire('Error', 'Terjadi kesalahan saat berkomunikasi dengan server.', 'error');
                    });
            },
            (error) => {
                console.error("Error getting location: ", error);
                Swal.fire('Error', 'Tidak dapat mengambil lokasi. Pastikan GPS atau layanan lokasi aktif dan berikan izin.', 'error');
            }
        );
    });
});