import { computed, toValue } from 'vue'
import { useBoardStore } from '../stores/boards'

const DEF = {
  card_label: '图片', cards_label: '图片', group_label: '图组', groups_label: '图组',
  appTitle: '',

  // frame words
  homeTitlePrefix: '', countUnit: '张', manageSuffix: '管理',
  addPrefix: '+ 添加', searchPrefix: '搜索',
  confirmDeletePrefix: '确定删除？这将同时删除该', confirmDeleteSuffix: '的所有数据。',
  noDataPrefix: '暂无', editTitlePrefix: '编辑', addTitlePrefix: '添加',
  tableNameSuffix: '名称', tableNumberSuffix: '号',

  // home / profile
  emptyHome: '', emptyHomeHint: '',
  homeLogin: '登录',
  myBoards: '我的画板', publicBoards: '公开画板',
  noPublicBoards: '该用户暂未公开任何画板',
  recentCards: '最近收录', publicCards: '公开作品',
  boardPublic: '公开', boardPrivate: '私密',
  adminButton: '管理后台', logoutButton: '退出登录', backHome: '返回首页',
  userNotFound: '用户不存在',
  userNotFoundHint: 'UID「{0}」没有对应的用户',

  // actions
  save: '保存', confirm: '确定', cancel: '取消', edit: '编辑', delete: '删除',
  loading: '加载中...', saveSuccess: '保存成功', createSuccess: '创建成功',
  saving: '保存中...',
  tagPlaceholder: '输入后回车添加', addTag: '添加', remove: '移除',

  // form labels
  remarkLabel: '来源', signatureLabel: '原图地址', locationLabel: '原作者',
  birthdayLabel: '生日', birthdayPlaceholder: '如 01-15',
  avatarLabel: '预览图 URL', importanceLabel: '评分', importanceNone: '未评分',
  circleTagsLabel: '标签', impressionTagsLabel: '印象标签',
  notesLabel: '图片描述', accountManageLabel: '账号管理',

  // confirm
  confirmDeleteAccount: '确定删除此账号？', confirmDeleteSimple: '确定删除？',

  // empty
  noAccounts: '暂无账号', noMembers: '暂无成员',

  // table
  tableAccounts: '账号', tableTags: '标签', tableImportance: '评分', tableActions: '操作',
  tableGroupRemark: '备注', tableGroupTags: '标签',

  // members dialog
  memberTitle: '成员', selectAccount: '选择账号', groupNicknameSuffix: '名片',

  // person detail
  personDetailNotFound: '', personDetailNotFoundHint: '「{0}」不存在或已被设置为私密',
  personDetailAccounts: '关联账号', personDetailMeetings: '备注', personDetailRelations: '相关信息',
  personDetailRelationFallback: '关联',

  // board
  defaultBoardName: '默认画板', defaultBoardIcon: '',
  newBoard: '+ 新建画板', boardNamePlaceholder: '画板名称',

  // settings page
  settingsTitle: '画板设置', boardNameLabel: '画板名称',
  iconLabel: '图标', descriptionLabel: '描述',
  appTitleLabel: '应用标题',
  cardSingleLabel: '卡片单数标签', cardPluralLabel: '卡片复数标签',
  groupSingleLabel: '分组单数标签', groupPluralLabel: '分组复数标签',
  frameWordsTitle: '框架文字设置', formLabelsTitle: '表单字段标签',
  allTextTitle: '全部文字覆盖', publicBoardLabel: '公开画板',
  publicVisible: '任何人可见', privateOnly: '仅自己可见',
  previewTitle: '预览效果（留空则使用默认值）',
  deleteBoard: '删除画板', deleteBoardConfirm: '确定删除此画板？所有数据将一并删除且不可恢复。',
  bannerImagesTitle: '卡片背景图片',
  bannerImagesHint: '上传、管理和查看所有图片请前往图床页面。',
  bannerImagesHelp: '卡片背景（设置分辨率）：卡片背景 URL > 图池随机 > 纯色占位。预览图仅用于详情页。',

  // images page
  imagesTitle: '图片管理（图床）',
  uploadImage: '+ 上传图片', uploading: '上传中...',
  imagesHint: '卡片背景从图池随机选取。可设置「卡片背景 URL」固定绑定。「预览图 URL」仅供详情页使用。',
  noImages: '暂无图片',
  copyUrl: '复制 URL', copied: '已复制',
  deleteImage: '删除', deleteImageConfirm: '从图池删除此图片？已使用此 URL 的作品不受影响。',
  uploadFail: '上传失败',

  // auth pages
  appName: '图片展示', loginTitle: '登录', registerTitle: '注册账号',
  usernamePlaceholder: '用户名', passwordPlaceholder: '密码',
  confirmPasswordPlaceholder: '确认密码',
  passwordHint: '密码（至少8位，含字母和数字）',
  loginButton: '登录', loggingIn: '登录中...',
  registerButton: '注册', registering: '注册中...',
  noAccount: '没有账号？', hasAccount: '已有账号？',
  loginValidation: '请输入用户名和密码',
  registerValidation: '请输入用户名和密码',
  passwordMismatch: '两次输入的密码不一致',
  passwordTooShort: '密码长度不能少于8位',
  registerSuccess: '注册成功！即将跳转到登录页...',
  avatarUploadFail: '头像上传失败', usernameChangeFail: '修改失败',
  changeAvatar: '换', changeUsernameHint: '双击修改用户名',
}

const TYPE_DEFAULTS = {
  image:  { card_label:'图片', cards_label:'图片', group_label:'图组', groups_label:'图组', icon:'' },
  friend: { card_label:'群友', cards_label:'群友们', group_label:'群', groups_label:'群组', icon:'' },
  shuoshuo:{ card_label:'说说', cards_label:'说说', group_label:'话题', groups_label:'话题', icon:'' },
}

export function useLabels(boardRef = null) {
  const boardStore = useBoardStore()

  return computed(() => {
    const board = toValue(boardRef)
    const b = board || boardStore.currentBoard || {}
    const fc = typeof b.field_config === 'object' ? b.field_config : {}

    const g = (key) => fc[key] || b[key] || DEF[key]
    const card = g('card_label')
    const cards = g('cards_label')
    const group = g('group_label')
    const groups = g('groups_label')
    const fmt = (key, ...args) => {
      let t = g(key) || ''
      args.forEach((a, i) => { t = t.replace(`{${i}}`, a != null ? String(a) : '') })
      return t
    }

    return {
      cardLabel: card, cardsLabel: cards, groupLabel: group, groupsLabel: groups,
      appTitle: fc.appTitle || card + '记忆助手',

      // navigation
      cardManage: card + g('manageSuffix'),
      groupManage: group + g('manageSuffix'),

      // home
      homeTitle: g('homeTitlePrefix') + cards,
      homeCount: (n) => n + ' ' + g('countUnit') + card,
      emptyHome: g('emptyHome') || '还没有' + card,
      homeLogin: g('homeLogin'),

      // profile
      myBoards: g('myBoards'), publicBoards: g('publicBoards'),
      noPublicBoards: g('noPublicBoards'),
      recentCards: g('recentCards'), publicCards: g('publicCards'),
      boardPublic: g('boardPublic'), boardPrivate: g('boardPrivate'),
      adminButton: g('adminButton'), logoutButton: g('logoutButton'), backHome: g('backHome'),
      userNotFound: g('userNotFound'),
      userNotFoundHint: (uid) => fmt('userNotFoundHint', uid),
      boardCardStatus: (bd) => (bd.cards_label || cards) + ' · ' + (bd.is_public ? g('boardPublic') : g('boardPrivate')),
      boardCardCount: (bd) => (bd.cards_count || 0) + ' ' + (bd.cards_label || cards),

      // actions
      addCard: g('addPrefix') + card, addGroup: g('addPrefix') + group,
      addCardTitle: g('addTitlePrefix') + card, editCardTitle: g('editTitlePrefix') + card,
      addGroupTitle: g('addTitlePrefix') + group, editGroupTitle: g('editTitlePrefix') + group,
      searchCard: g('searchPrefix') + card + '...', searchGroup: g('searchPrefix') + group + '...',

      // form
      cardNameLabel: card + g('tableNameSuffix') + ' *',
      remarkLabel: g('remarkLabel'), signatureLabel: g('signatureLabel'),
      locationLabel: g('locationLabel'), birthdayLabel: g('birthdayLabel'),
      birthdayPlaceholder: g('birthdayPlaceholder'), avatarLabel: g('avatarLabel'),
      importanceLabel: g('importanceLabel'), importanceNone: g('importanceNone'),
      circleTagsLabel: g('circleTagsLabel'), impressionTagsLabel: g('impressionTagsLabel'),
      notesLabel: g('notesLabel'), accountManageLabel: g('accountManageLabel'),

      // confirm
      confirmDeleteCard: g('confirmDeletePrefix') + card + g('confirmDeleteSuffix'),
      confirmDeleteAccount: g('confirmDeleteAccount'),
      confirmDeleteGroup: fmt('confirmDeleteGroup', group) || '确定删除此' + group + '？',
      confirmDeleteSimple: g('confirmDeleteSimple'),

      // empty
      noData: g('noDataPrefix') + card,
      noAccounts: g('noAccounts'), noMembers: g('noMembers'),

      // table
      tableCard: card, tableAccounts: g('tableAccounts'), tableTags: g('tableTags'),
      tableImportance: g('tableImportance'), tableActions: g('tableActions'),
      tableGroupName: group + g('tableNameSuffix'), tableGroupNumber: group + g('tableNumberSuffix'),
      tableGroupRemark: g('tableGroupRemark'), tableGroupTags: g('tableGroupTags'),

      // members dialog
      memberTitle: g('memberTitle'), selectAccount: g('selectAccount'),
      groupNickname: group + g('groupNicknameSuffix'),

      // generic
      save: g('save'), confirm: g('confirm'), cancel: g('cancel'),
      edit: g('edit'), delete: g('delete'), loading: g('loading'),
      saveSuccess: g('saveSuccess'), createSuccess: g('createSuccess'), saving: g('saving'),
      tagPlaceholder: g('tagPlaceholder'), addTag: g('addTag'), remove: g('remove'),

      // person detail
      personDetailNotFound: g('personDetailNotFound') || '找不到这位' + card,
      personDetailNotFoundHint: (name) => fmt('personDetailNotFoundHint', name),
      personDetailAccounts: g('personDetailAccounts'),
      personDetailMeetings: g('personDetailMeetings'),
      personDetailRelations: g('personDetailRelations'),
      personDetailRelationFallback: g('personDetailRelationFallback'),

      // board
      defaultBoardName: g('defaultBoardName'), defaultBoardIcon: g('defaultBoardIcon'),
      newBoard: g('newBoard'), boardNamePlaceholder: g('boardNamePlaceholder'),

      // settings page
      settingsTitle: g('settingsTitle'), boardNameLabel: g('boardNameLabel'),
      iconLabel: g('iconLabel'), descriptionLabel: g('descriptionLabel'),
      appTitleLabel: g('appTitleLabel'),
      cardSingleLabel: g('cardSingleLabel'), cardPluralLabel: g('cardPluralLabel'),
      groupSingleLabel: g('groupSingleLabel'), groupPluralLabel: g('groupPluralLabel'),
      frameWordsTitle: g('frameWordsTitle'), formLabelsTitle: g('formLabelsTitle'),
      allTextTitle: g('allTextTitle'), publicBoardLabel: g('publicBoardLabel'),
      publicVisible: g('publicVisible'), privateOnly: g('privateOnly'),
      previewTitle: g('previewTitle'),
      deleteBoard: g('deleteBoard'), deleteBoardConfirm: g('deleteBoardConfirm'),
      bannerImagesTitle: g('bannerImagesTitle'),
      bannerImagesHint: g('bannerImagesHint'), bannerImagesHelp: g('bannerImagesHelp'),

      // images page
      imagesTitle: g('imagesTitle'), uploadImage: g('uploadImage'), uploading: g('uploading'),
      imagesHint: g('imagesHint'), noImages: g('noImages'), noImagesHint: g('noImagesHint'),
      copyUrl: g('copyUrl'), copied: g('copied'), deleteImage: g('deleteImage'),
      deleteImageConfirm: g('deleteImageConfirm'), uploadFail: g('uploadFail'),

      // auth pages
      appName: g('appName'), loginTitle: g('loginTitle'), registerTitle: g('registerTitle'),
      usernamePlaceholder: g('usernamePlaceholder'), passwordPlaceholder: g('passwordPlaceholder'),
      confirmPasswordPlaceholder: g('confirmPasswordPlaceholder'),
      passwordHint: g('passwordHint'), loginButton: g('loginButton'), loggingIn: g('loggingIn'),
      registerButton: g('registerButton'), registering: g('registering'),
      noAccount: g('noAccount'), hasAccount: g('hasAccount'),
      loginValidation: g('loginValidation'), registerValidation: g('registerValidation'),
      passwordMismatch: g('passwordMismatch'), passwordTooShort: g('passwordTooShort'),
      registerSuccess: g('registerSuccess'),
      avatarUploadFail: g('avatarUploadFail'), usernameChangeFail: g('usernameChangeFail'),
      changeAvatar: g('changeAvatar'), changeUsernameHint: g('changeUsernameHint'),
    }
  })
}

export { DEF, TYPE_DEFAULTS }
