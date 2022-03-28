from tkinter import *
from tkinter import filedialog
import tkinter.ttk as ttk
import tkinter.messagebox as msgbox
import youtube_dl, os, ffmpeg, glob, re, threading, datetime
import pandas as pd


# Base
root = Tk()
root.iconbitmap('Fiva.ico')
root.title("YouTube_Down_Loader")

# <필요 전역 변수>
dir_name = list()
total_down=list()
down_success=list()
play_list_URL = list()
log_path = os.getcwd()
inter_state = 'disable'
Option={'format':'bestvideo+bestaudio/best','extension':'.mp4','chk_leak':1}
p = re.compile('http[s]?://(?:[a-zA-Z]|[0-9]|[$\-@\.&+:/?=]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')


# Print Message At State Window : Must Be Use '+'(Plus Factor) When Connect String to String( Or Between Same Data Type )
def print_state(msg, msg_type='info'):
    show_info.config(state='normal')
    if msg_type=='info' :
        show_info.insert(END, msg+'\n')
    elif msg_type=='error' :
        show_info.insert(END, msg+'\n','warning')
    show_info.see(END)
    show_info.config(state='disable')

def log(log_data, target=log_path) :
    log_append = open(log_path+'\log.txt','a',encoding='utf-8')
    log_append.write((log_data+'\n'))
    log_append.close()

# Add File With File Explorer
def add_file():
    files = filedialog.askopenfilename(title="Select Img File",\
                                       filetypes=(("Excel File", "*.csv"), ("All File", "*.*")))
    if files == '' : return
    data = pd.read_csv(files,encoding='EUC-KR')
    for i in range(len(data)):
        dir_name.append(data.get('DirName')[i])
        play_list_URL.append(data.get('List_URL')[i])
        total_down.append((data.get('DirName')[i],data.get('List_URL')[i]))

    for i in range(len(data)):
        list_url.insert('', 'end',values=(data.get('DirName')[i],data.get('List_URL')[i]))

    print_state('Add File !')

# Delete URL
def del_url():
    del_item_len = len(list_url.selection())
    if del_item_len == 0 :
        print_state('Please Select Delete URL !','error')
        return
    for i in range(len(play_list_URL)):
        if play_list_URL[i]==list_url.item(list_url.focus()).get('values')[1] :
            del dir_name[i]
            del play_list_URL[i]
            del total_down[i]
            break
    for i in list_url.selection() :
        list_url.delete(i)
        print_state('Delete '+str(del_item_len)+' items!')

# Add URL
def add_url():
    if len(total_down) != 0 :
        for i in range(len(play_list_URL)) :
            if add_url_text.get() == play_list_URL[i] :
                msgbox.showwarning('URL Overlap','Input URL Already Exist ! ')
                add_url_text.delete("0", "end")
                return
    if p.match(add_url_text.get()) :
        list_url.insert('', 'end', values=['General', add_url_text.get()])
        dir_name.append('General')
        play_list_URL.append(add_url_text.get())
        total_down.append(('General',add_url_text.get()))
        add_url_text.delete("0", "end")
    else :
        msgbox.showinfo('Fail', 'Insert Only URL Standard!')
        add_url_text.delete("0", "end")

# Add URL Event Binding With 'Enter'
def get_url_enter(event):
    add_url()

# Cursor On URL Input Window : Delete PlaceHolder
def url_window_click(event):
    if add_url_text.get() == 'Insert URL Here' :
        add_url_text.delete("0", "end")

# Select Save Path
def save_path():
    fol_sel = filedialog.askdirectory()
    if fol_sel == '':
        return
    txt_path.delete(0, END)
    txt_path.insert(0, fol_sel)

# Select Available Extension When 'Video' Selected
def ava_extension():
    if rv.get() == '.mp3' :
        sel_ext.config(stat='disable')
        rd1.focus_set()
    else :
        sel_ext.config(stat='readonly')
        rd2.focus_set()

# Get Option
def get_option():
    if rv.get() == '.mp3' :
        Option['format'] = 'bestaudio/best'
        Option['extension'] = '.mp3'
    else :
        Option['format'] = 'bestvideo+bestaudio/best'
        Option['extension'] = sel_ext.get()
    Option['chk_leak'] = chk_leak_option.get()

# Interaction Change : Disable When Download File
def Interaction() :
    global inter_state
    btn_del_list.config(stat=inter_state)
    btn_add_url.config(state=inter_state)
    btn_add_file.config(state=inter_state)
    add_url_text.config(state=inter_state)
    txt_path.config(state=inter_state)
    btn_path.config(state=inter_state)
    rd1.config(state=inter_state)
    chk_leak_btn.config(state=inter_state)
    rd2.config(state=inter_state)
    sel_ext.config(state=inter_state)
    if inter_state=='disable' :
        inter_state = 'normal'
    else : inter_state='disable'

# Option Check : Have NULL
def chk_null():
    if len(play_list_URL) == 0:
        msgbox.showwarning("Warning", "Input Target URL !")
        return 1
    if len(txt_path.get()) == 0:
        msgbox.showwarning("Warning", "Select Save Directory !")
        return 1
    if rv.get() == '':
        msgbox.showwarning("Warning", "Select Format Option !")
        return 1
    else :
        Interaction()
        return 0

# Progress Hook : Processing When Get Update Progress Information
def my_hook(d):
    comp_name = os.path.splitext(os.path.basename(d['filename']))[0]
    if down_file_name.cget('text') != comp_name :
        down_file_name.config(text=comp_name)
        down_success.append(comp_name)
        threading.Thread(target=log('[파일정보] '+str(d)))

       # Initialize Progress Bar
        down_per=0
        p_var.set(down_per)
        pb.update()

        # Update Down Count
        prgs_show = file_prgs_show.cget('text')
        m = int(len(prgs_show) / 2) if len(prgs_show)%2 != 0 else int(len(prgs_show) / 2)-1
        file_prgs_show.config(text=str(int(prgs_show[:m]) + 1) + prgs_show[m:])

    if d['status'] != 'finished' :
        p_var.set(float(d['_percent_str'][:-1]))
        pb.update()

# Count Total Download File
def count_total_down():
    print_state('\n[다운로드 파일 목록 계산]')
    count_total = 0
    ydl = youtube_dl.YoutubeDL()
    for URL in play_list_URL :
        r = ydl.extract_info(URL,download=False) # 선 처리 과정에서 Entire 정보를 가지고 있음
        if '_type' in r :
            count_total += int(r['entries'][1]['n_entries'])
            continue
        else :
            count_total += 1
            continue
    print_state(' -> 완료 : '+str(count_total)+'개의 항목 확인')
    file_prgs_show.config(text='0/'+str(count_total))
    return count_total

# Change Format
# Other Ver : Rename File That Only Have Not Extension -> 기각 : 파일 중간에 구분자가 들어가 있으면 오작동
def chg_format(op):
    global down_success
    down_success = list(down_success)
    if  Option['extension'] == 'Original' : return True
    print_state('\n[확장자 변경작업 시작]')
    work_dir_path = list()
    for dir in dir_name :
        work_dir_path.append(txt_path.get()+'/'+dir+'/')
    work_dir_path = set(work_dir_path)
    for dir in work_dir_path :
        os.chdir(dir)
        print_state(re.sub(txt_path.get(),"",dir)[1:-1]+'의 확장자 변경 작업 시작')
        log(re.sub(txt_path.get(),"",dir)[1:-1]+'의 확장자 변경 작업 시작')
        for download_file in os.listdir(dir) :
            if os.path.splitext(download_file)[0] in down_success and os.path.splitext(download_file)[1] != op :
                os.rename(download_file, os.path.splitext(download_file)[0]+op)
                print_state(' -> '+download_file+'의 확장자 변경 성공')
                log(' -> '+download_file+'의 확장자 변경 성공')
    print_state(' -> 확장자 변경 작업 종료')
    log(' -> 확장자 변경 작업 종료')

# Check Leak File Using List
def check_leak() :
    print_state('\n[누락검사 시작]')
    log('누락검사 시작')
    global down_success
    down_success = set(down_success)
    dir_list=set()
    for dir in dir_name :
        dir_list = dir_list | set(os.listdir(txt_path.get()+'/'+dir+'/'))
    dir_list = list(dir_list)
    for file in range(len(dir_list)) :
        dir_list[file] = os.path.splitext(dir_list[file])[0]
    leak_file = down_success - set(dir_list)
    if len(leak_file) == 0 :
        print_state(' -> 누락파일 없음')
        log(' -> 누락파일 없음')
    else :
        for leak in leak_file :
            print_state(' -> [누락] '+leak,'error')
            log(' -> [누락] '+str(leak))

# Initialize
def init_all():
    os.chdir(log_path)
    log(str(datetime.datetime.now()) + ' 다운로드 완료. 변수 및 설정 초기화.\n')
    dir_name.clear()
    play_list_URL.clear()
    total_down.clear()
    for i in list_url.get_children() :
        list_url.delete(i)
    txt_path.delete(0, END)
    rd2.select()
    chk_leak_btn.select()
    down_file_name.config(text='down_file_name')
    file_prgs_show.config(text='0 / 0')
    p_var.set(0)
    pb.update()
    for i in range(3):
        print_state('\n')
    print_state('모든 파일은 최고화질/음질로 다운로드\n')
    start_thread = threading.Thread(target=start).start
    btn_start.config(command=start_thread)

# Start Main
def start():
    if chk_null() :
        start_thread = threading.Thread(target=start).start
        return 0
    log(str(datetime.datetime.now())+' 다운로드 시작')
    log('[입력 URL] '+str(play_list_URL))
    get_option()
    count_total_down()
    print_state('\n[다운로드 시작]')
    try:
        for cnt in range(len(dir_name)):
            try:
                if not (os.path.isdir(txt_path.get()+'/'+dir_name[cnt])):
                    os.makedirs(os.path.join(txt_path.get()+'/'+dir_name[cnt]))
            except OSError as e:
                if e.errno != errno.EEXIST:
                    print_state(('Fail Create Directory - '+dir_name[cnt]),'error')
                    exit()

            # DownLoad Main
            output_dir = os.path.join(txt_path.get()+'/'+dir_name[cnt] + '\%(title)s')
            ydl_opt = {'format': Option['format'], 'outtmpl': output_dir,'progress_hooks': [my_hook]}
            with youtube_dl.YoutubeDL(ydl_opt) as ydl:
                ydl.download([play_list_URL[cnt]])
        print_state(' -> 다운로드 종료\n')
        check_leak() if Option['chk_leak'] else print_state('[누락파일검사 생략]')
        chg_format(Option['extension'])
        msgbox.showinfo(title='Success', message='Success Download !')
        Interaction()
        init_all()
        return 0
    except Exception as exc :
        print_state('[Error]'+str(exc),'error')
        print('\n[Error]'+str(exc),'error')
        log('[Error]'+str(exc))

# Check Grid Area : ,relief="groove"
# Select File / Add URL
file_frame = Frame(root)
file_frame.pack(fill='x', padx=5, pady=5)
btn_del_list = Button(file_frame, text='Delete', width=9, height=1, command=del_url)
btn_del_list.pack(side='right', padx=2)
btn_add_file = Button(file_frame, text='Add File', width=9, height=1, command=add_file)
btn_add_file.pack(side='right')
btn_add_url = Button(file_frame, text='Add URL', width=9, height=1, command=add_url)
btn_add_url.pack(side='right', padx=2)
add_url_text = Entry(file_frame, width=40)
add_url_text.pack(side='right',ipady=2)
add_url_text.insert(0, "Insert URL Here")
add_url_text.bind('<Return>', get_url_enter)
add_url_text.bind('<1>', url_window_click)

# File List That Selected
list_frame = Frame(root)
list_frame.pack(fill='both', padx=5, pady=5)
scroll = Scrollbar(list_frame)
scroll.pack(side='right', fill='y')
list_url = ttk.Treeview(list_frame, columns=["List_Name","URL"], displaycolumns=["List_Name","URL"],selectmode='extended', height=10, yscrollcommand=scroll.set)
list_url.pack(side='left', fill='both', expand=True)
list_url.column('#0',width=0, stretch=NO)
list_url.column('#1', anchor='center',width=0)
list_url.heading('List_Name',text='List Name', anchor='center')
list_url.column('#2', anchor='center',width=250)
list_url.heading('URL',text='URL', anchor='center')
scroll.config(command=list_url.yview)

# Save Path
path_frame = LabelFrame(root, text="Save Path")
path_frame.pack(fill='x', padx=5, pady=5, ipady=5)
txt_path = Entry(path_frame)
txt_path.pack(side='left', fill='x', expand=True, padx=5, pady=5, ipady=4)
btn_path = Button(path_frame, text='Select', width=10, command=save_path)
btn_path.pack(side='right', padx=5, pady=5)

# Select Option
option_frame = LabelFrame(root, text='Option')
option_frame.pack(fill='x', padx=5, pady=5, ipady=5)
rv = StringVar()
rd1 = Radiobutton(option_frame, text="Mp3",width=6,value='.mp3',anchor=W, variable=rv, command=ava_extension)
rd1.grid(row=0,column=0)
chk_leak_option = IntVar()
chk_leak_btn = Checkbutton(option_frame, text="누락 검사",variable=chk_leak_option,anchor=E)
chk_leak_btn.grid(row=0,column=1,sticky=E)
chk_leak_btn.select()
rd2 = Radiobutton(option_frame, text="Video",width=6,anchor=W, value='video', variable=rv, command=ava_extension)
rd2.select()
rd2.grid(row=1,column=0)
extension=['.mp4','.avi','.mkv','.wmv','Original']
sel_ext = ttk.Combobox(option_frame, width=10, values=extension, stat="readonly")
sel_ext.current(0)
sel_ext.grid(row=1,column=1)

# Show Progress
frame_prog = LabelFrame(root, text='Progress State')
frame_prog.pack(fill='x', padx=5, pady=5, ipady=5)
p_var = DoubleVar()
down_file_name = Label(frame_prog,width=61,text='down_file_name',anchor=W)
down_file_name.grid(row=0,column=0,pady=5)
file_prgs_desc=Label(frame_prog,width=5,text='진행 :',anchor=E)
file_prgs_desc.grid(row=0,column=1,pady=5)
file_prgs_show=Label(frame_prog,width=4,text='0 / 0',anchor='center')
file_prgs_show.grid(row=0,column=2,pady=5)
pb = ttk.Progressbar(frame_prog,maximum=100,variable=p_var)
pb.grid(row=1,column=0,columnspan=3,sticky=W+E,pady=5)
show_info = Text(frame_prog,height=5,width=72,wrap=NONE)
show_info.insert(END,'모든 파일은 최고화질/음질로 다운로드\n')
show_info.config(state='disable')
show_info.grid(row=2,column=0,columnspan=3)
# Tag for print progress(show_info)
show_info.tag_config('warning', foreground="red", font='bold')

# Start / Clear : Use Threading On 'Start' Method
frame_run = Frame(root)
start_thread = threading.Thread(target=start).start
frame_run.pack(fill='x', padx=5, pady=5)
btn_close = Button(frame_run, padx=5, pady=5, width=10, text="Close", command=root.quit)
btn_close.pack(side='right', padx=5, pady=5)
btn_start = Button(frame_run, padx=5, pady=5, width=10, text="Start", command=start_thread)
btn_start.pack(side='right', padx=5, pady=5)

log('\n[ON] '+str(datetime.datetime.now())+' 다운로더 작동시작')
root.resizable(False, False)
root.mainloop()

# 21.08.01 YouTube_Downloader-GUI Ver 1.0 작성 완료
# 소요기간 : 약 60일