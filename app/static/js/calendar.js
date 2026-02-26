// Calendar component for date and time selection

class Calendar {
    constructor(containerId, serviceId) {
        this.container = document.getElementById(containerId);
        this.serviceId = serviceId;
        this.currentDate = new Date();
        this.selectedDate = null;
        this.selectedTimeSlot = null;
        
        this.init();
    }
    
    init() {
        this.render();
        this.attachEventListeners();
    }
    
    attachEventListeners() {
        document.getElementById('prevMonth').addEventListener('click', () => {
            this.currentDate.setMonth(this.currentDate.getMonth() - 1);
            this.render();
        });
        
        document.getElementById('nextMonth').addEventListener('click', () => {
            this.currentDate.setMonth(this.currentDate.getMonth() + 1);
            this.render();
        });
    }
    
    render() {
        const year = this.currentDate.getFullYear();
        const month = this.currentDate.getMonth();
        
        // Update month display
        const monthNames = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
                           'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'];
        document.getElementById('currentMonth').textContent = `${monthNames[month]} ${year}`;
        
        // Clear calendar
        this.container.innerHTML = '';
        
        // Get first day of month and number of days
        const firstDay = new Date(year, month, 1).getDay();
        const daysInMonth = new Date(year, month + 1, 0).getDate();
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        
        // Add day headers
        const dayHeaders = ['Вс', 'Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб'];
        dayHeaders.forEach(day => {
            const header = document.createElement('div');
            header.style.fontWeight = 'bold';
            header.style.textAlign = 'center';
            header.style.padding = '10px';
            header.textContent = day;
            this.container.appendChild(header);
        });
        
        // Add empty cells for days before month starts
        for (let i = 0; i < firstDay; i++) {
            const emptyCell = document.createElement('div');
            this.container.appendChild(emptyCell);
        }
        
        // Add day cells
        for (let day = 1; day <= daysInMonth; day++) {
            const date = new Date(year, month, day);
            date.setHours(0, 0, 0, 0); // Reset time to midnight
            const dayCell = document.createElement('div');
            dayCell.className = 'calendar-day';
            dayCell.textContent = day;
            
            // Disable past dates (before today)
            if (date < today) {
                dayCell.classList.add('disabled');
            } else {
                dayCell.addEventListener('click', () => this.selectDate(date));
            }
            
            this.container.appendChild(dayCell);
        }
    }
    
    async selectDate(date) {
        this.selectedDate = date;
        
        // Update selected state
        document.querySelectorAll('.calendar-day').forEach(cell => {
            cell.classList.remove('selected');
        });
        
        // Find and select the clicked day cell
        const dayCells = Array.from(document.querySelectorAll('.calendar-day'));
        const clickedCell = dayCells.find(cell => 
            parseInt(cell.textContent) === date.getDate() && 
            !cell.classList.contains('disabled')
        );
        if (clickedCell) {
            clickedCell.classList.add('selected');
        }
        
        // Format date for display
        const dateStr = date.toLocaleDateString('ru-RU', {
            day: 'numeric',
            month: 'long',
            year: 'numeric'
        });
        document.getElementById('selectedDateDisplay').textContent = dateStr;
        
        // Store date in hidden input - use local date string to avoid timezone issues
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        const isoDate = `${year}-${month}-${day}`;
        
        console.log('Selected date:', isoDate); // Debug log
        document.getElementById('selectedDate').value = isoDate;
        
        // Fetch available time slots
        await this.fetchTimeSlots(isoDate);
        
        // Show time slots container
        document.getElementById('timeSlotsContainer').classList.remove('hidden');
        
        // Hide form until time slot is selected
        document.getElementById('bookingFormContainer').classList.add('hidden');
    }
    
    async fetchTimeSlots(date) {
        try {
            const response = await fetch(`/api/slots?date=${date}`);
            const data = await response.json();
            
            if (data.error) {
                alert(data.error);
                return;
            }
            
            this.renderTimeSlots(data.slots);
        } catch (error) {
            console.error('Error fetching time slots:', error);
            alert('Ошибка загрузки доступного времени');
        }
    }
    
    renderTimeSlots(slots) {
        const container = document.getElementById('timeSlots');
        container.innerHTML = '';
        
        // Check if selected date is today
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        const isToday = this.selectedDate && this.selectedDate.getTime() === today.getTime();
        
        // Get current time if today
        let currentHour = 0;
        if (isToday) {
            const now = new Date();
            currentHour = now.getHours();
        }
        
        // Don't filter slots - show all, but mark past ones as unavailable
        const processedSlots = slots.map(slot => {
            if (isToday) {
                const [hour] = slot.time.split(':').map(Number);
                // Mark as unavailable if hour is not greater than current hour
                if (hour <= currentHour) {
                    return { ...slot, available: false, isPast: true };
                }
            }
            return slot;
        });
        
        // Group slots by hour
        const hourlyGroups = this.groupSlotsByHour(processedSlots);
        
        // Create horizontal container for hourly slots
        const horizontalContainer = document.createElement('div');
        horizontalContainer.className = 'hourly-slots-horizontal';
        
        // Render each hourly group
        hourlyGroups.forEach(group => {
            const hourlySlot = this.createHourlySlot(group);
            horizontalContainer.appendChild(hourlySlot);
        });
        
        container.appendChild(horizontalContainer);
    }
    
    groupSlotsByHour(slots) {
        const groups = {};
        
        slots.forEach(slot => {
            const hour = slot.time.split(':')[0];
            if (!groups[hour]) {
                groups[hour] = {
                    hour: hour,
                    slots: []
                };
            }
            groups[hour].slots.push(slot);
        });
        
        // Sort groups by hour numerically
        return Object.values(groups).sort((a, b) => {
            return parseInt(a.hour) - parseInt(b.hour);
        });
    }
    
    createHourlySlot(group) {
        const hourlyContainer = document.createElement('div');
        hourlyContainer.className = 'hourly-slot-container';
        
        // Check if all slots in this hour are unavailable
        const allUnavailable = group.slots.every(slot => !slot.available);
        
        // Create hourly header (expandable)
        const hourlyHeader = document.createElement('div');
        hourlyHeader.className = 'hourly-slot-header';
        if (allUnavailable) {
            hourlyHeader.classList.add('disabled');
        }
        
        // Add arrow icon
        const arrow = document.createElement('span');
        arrow.className = 'arrow-icon';
        arrow.innerHTML = '▼';
        
        // Add hour text
        const hourText = document.createElement('span');
        hourText.textContent = `${group.hour}:00`;
        
        hourlyHeader.appendChild(arrow);
        hourlyHeader.appendChild(hourText);
        
        // Create 15-minute slots container (initially hidden)
        const slotsContainer = document.createElement('div');
        slotsContainer.className = 'minute-slots-container hidden';
        
        group.slots.forEach(slot => {
            const slotEl = document.createElement('div');
            slotEl.className = 'time-slot minute-slot';
            slotEl.textContent = slot.time;
            
            if (!slot.available) {
                slotEl.classList.add('unavailable');
                slotEl.title = slot.isPast ? 'Время прошло' : 'Время занято';
            } else {
                slotEl.addEventListener('click', () => this.selectTimeSlot(slot.time, slotEl));
            }
            
            slotsContainer.appendChild(slotEl);
        });
        
        // Add click handler to toggle expansion (only if not all unavailable)
        if (!allUnavailable) {
            hourlyHeader.addEventListener('click', () => {
                const isExpanded = !slotsContainer.classList.contains('hidden');
                
                if (isExpanded) {
                    // Close this one
                    slotsContainer.classList.add('hidden');
                    arrow.innerHTML = '▼';
                    hourlyContainer.classList.remove('expanded');
                } else {
                    // Close all other expanded slots first
                    document.querySelectorAll('.hourly-slot-container.expanded').forEach(container => {
                        const otherSlotsContainer = container.querySelector('.minute-slots-container');
                        const otherArrow = container.querySelector('.arrow-icon');
                        if (otherSlotsContainer) {
                            otherSlotsContainer.classList.add('hidden');
                        }
                        if (otherArrow) {
                            otherArrow.innerHTML = '▼';
                        }
                        container.classList.remove('expanded');
                    });
                    
                    // Open this one
                    slotsContainer.classList.remove('hidden');
                    arrow.innerHTML = '▲';
                    hourlyContainer.classList.add('expanded');
                }
            });
        }
        
        hourlyContainer.appendChild(hourlyHeader);
        hourlyContainer.appendChild(slotsContainer);
        
        return hourlyContainer;
    }
    
    selectTimeSlot(timeSlot, element) {
        this.selectedTimeSlot = timeSlot;
        
        // Update selected state - only for minute slots
        document.querySelectorAll('.minute-slot').forEach(slot => {
            slot.classList.remove('selected');
        });
        element.classList.add('selected');
        
        // Store time slot in hidden input
        document.getElementById('selectedTimeSlot').value = timeSlot;
        
        // Show booking form
        document.getElementById('bookingFormContainer').classList.remove('hidden');
        
        // Scroll to form
        document.getElementById('bookingFormContainer').scrollIntoView({
            behavior: 'smooth',
            block: 'start'
        });
    }
}
